import imutils
import time
import cv2
import os
import sys
import math
import numpy as np


class RatedContour:
    def __init__(self, contour, maxX, maxY, img):
        self.contour = contour
        self.maxX = maxX
        self.maxY = maxY
        self.img = img;

        # calculate useful values
        self.x, self.y, self.w, self.h = cv2.boundingRect(self.contour)
        self.rating = self.rating()
        self.ratingAsColor = (25 * (self.rating + 5))

    def rating(self):
        ratingStepCount = 5
        # range of rating is between -1.0 and +1.0
        ratingValue = 0.0

        self.M = cv2.moments(self.contour)  # moments
        area = self.M['m00']
        hull = cv2.convexHull(self.contour)

        # rate based on x position (centroid x)
        self.cx = int(self.M['m10'] / self.M['m00'])
        self.cy = int(self.M['m01'] / self.M['m00'])
        diffCenter = abs(self.maxX / 2 - self.cx)
        # self.xRating = ((2/(self.maxX/2))*diffCenter)
        self.xRating = (2 - (2 / (self.maxX / 2) * diffCenter)) - 1
        ratingValue += self.xRating

        # rate based on area
        self.areaRating = ((2 / 4000) * area) - 1
        ratingValue += self.areaRating

        # rate based on mean intensity
        cmask = np.zeros(self.img.shape, np.uint8)
        cv2.drawContours(cmask, [self.contour], 0, 255, -1)
        meanVal = cv2.mean(self.img, mask=cmask)
        # self.meanRating = (float(2/80)*float(meanVal[0]))-1
        self.meanRating = (2 - np.clip((2 / 30) * float(meanVal[0]), 0, 2)) - 1
        ratingValue = ratingValue + self.meanRating

        # rate based on solidity (ratio of pixels to overall area)
        '''
        hull_area = cv2.contourArea(hull)
        if(hull_area > 0):
            solidity = float(area)/hull_area
            self.solidityRating = ((2/1.66)*solidity)-1
        else:
            self.solidityRating = 0
        ratingValue = ratingValue + self.solidityRating
        '''

        # rate based on ellipse filling factor
        self.ellipse = cv2.fitEllipse(self.contour)
        ellArea = (math.pi * self.ellipse[1][0] / 2 * self.ellipse[1][1] / 2)
        self.ellipseRating = (2 - (np.clip(abs(1 - (ellArea / area)), 0, 2))) - 1
        ratingValue = ratingValue + self.ellipseRating

        # rate based on circularity / "ellipseness"
        circularity = float(self.ellipse[1][0]) / self.ellipse[1][1]
        self.circRating = (2 - (np.clip(abs(1 - circularity), 0, 2))) - 1
        ratingValue = ratingValue + self.circRating

        # normalize
        ratingValue /= ratingStepCount

        # return
        return ratingValue
