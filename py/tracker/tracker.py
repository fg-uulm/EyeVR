"""
TODOs

## Recognition
- Search Space Minimization based on last position
- Autogain
- Glint Persistence


"""

# import the necessary packages
from __future__ import print_function
from imutils.video import FPS
import time
import cv2
import numpy as np
from tracker.OneEuroFilter import OneEuroFilter
from tracker.RatedContour import RatedContour
from tracker.PulseDetector import findFaceGetPulse
import settings as s


### VARS
width = 320
height = 240

yOffTop = -120
yOffBot = 70
xOffLeft = -70
xOffRight = 190

fps = FPS().start()
maxLoc = (0, 0)
calfile = "intrinsics_calibrations/calib_1465396371267.npz"
autothres_divisor = 1.0
eyearea_copy = np.zeros((height, width, 3), np.uint8)
gray = np.zeros((height, width, 3), np.uint8)

class Tracker:
    @staticmethod
    def auto_canny(image, sigma=0.33):
        # compute the median of the single channel pixel intensities
        v = np.median(image)

        # apply automatic Canny edge detection using the computed median
        lower = int(max(0, (1.0 - sigma) * v))
        upper = int(min(255, (1.0 + sigma) * v))
        edged = cv2.Canny(image, lower, upper)

        # return the edged image
        return edged

    @staticmethod
    def adjust_gamma(image, gamma=1.0):
        # build a lookup table mapping the pixel values [0, 255] to
        # their adjusted gamma values
        invGamma = 1.0 / gamma
        table = np.array([((i / 255.0) ** invGamma) * 255
                          for i in np.arange(0, 256)]).astype("uint8")

        # apply gamma correction using the lookup table
        return cv2.LUT(image, table)


    def analyzr(self):
        print("Tracker startup")

        maxLoc = (s.SETTINGS['xOffLeft'] * -1, s.SETTINGS['yOffTop'] * -1)
        blink = True

        # load calibration for applying later
        cf = np.load(calfile)
        print(cf.files)

        # prepare filters for later use
        config = {
            'freq': 40,  # Hz
            'mincutoff': 2.05,  # FIXME
            'beta': 0.1,  # FIXME
            'dcutoff': 1.0  # this one should be ok
        }

        glintFilterX = OneEuroFilter(**config)
        glintFilterY = OneEuroFilter(**config)
        pupilFilterX = OneEuroFilter(**config)
        pupilFilterY = OneEuroFilter(**config)
        pupilFilterH = OneEuroFilter(**config)
        pupilFilterW = OneEuroFilter(**config)
        bpmFilter = OneEuroFilter(**config)

        # experimental: heartrate / pulse detector (see https://github.com/thearn/webcam-pulse-detector)
        self.processor = findFaceGetPulse(bpm_limits=[50, 160],
                                          data_spike_limit=2500.,
                                          face_detector_smoothness=10.)

        while True:
            # do teh heavy lifting here
            #
            # first: detect cornea reflex
            #
            time.sleep(0.001)
            frame = s.FRMPROV.nextFrame()
            #s.logAppend("Start Processing Frame")

            # flip
            if (s.SETTINGS['flip']):
                frame = cv2.flip(frame, -1)

            # Experimental: pulse detection
            if(s.SETTINGS['heartRateEnabled']):
                # set current image frame to the processor's input
                self.processor.frame_in = frame
                # process the image frame to perform all needed analysis
                self.processor.run()

            # convert to grayscale
            #s.OUT_IMGRAW = frame.copy()
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

            # undistort
            if (s.SETTINGS["undistort"]):
                h, w = gray.shape[:2]
                newcameramtx, roi = cv2.getOptimalNewCameraMatrix(cf['mtx'], cf['dist'], (w, h), 1, (w, h))
                gray = cv2.undistort(gray, cf['mtx'], cf['dist'], None, newcameramtx)

            # optional equalization
            if (s.SETTINGS["equalize"]):
                # gray = cv2.equalizeHist(gray);
                clahe = cv2.createCLAHE(clipLimit=s.SETTINGS['claheClipLimit'], tileGridSize=(8, 8))
                gray = clahe.apply(gray)

            grayblur = cv2.blur(gray, (s.SETTINGS['grayBlurRadius'], s.SETTINGS['grayBlurRadius']))
            #s.OUT_IMGRAW = gray.copy()

            try:
                # find corneal glint location
                (minVal, maxVal, minLoc, maxLocTmp) = cv2.minMaxLoc(grayblur)
                # only use if bright spot is really bright, otherwise let filter interpolate
                if (maxVal > s.SETTINGS['minSpotBrightness']):
                    maxLoc = maxLocTmp
                    blink = False
                else:
                    blink = True

                # filter
                if (s.SETTINGS['filtering_glint']):
                    maxLoc = (glintFilterX(maxLoc[0], int(round(time.time() * 1000))),
                              glintFilterY(maxLoc[1], int(round(time.time() * 1000))))

                # extract eye area based on glint location
                eyearea = gray[int(maxLoc[1]) + s.SETTINGS['yOffTop']:int(maxLoc[1]) + s.SETTINGS['yOffBot'], int(maxLoc[0]) + s.SETTINGS['xOffLeft']:int(maxLoc[0]) + s.SETTINGS['xOffRight']]
                if (eyearea.shape[0] == 0 or eyearea.shape[1] == 0 or blink):
                    eyearea = gray

                eyearea_src = eyearea.copy()

                # optional contrast / brightness enhancement
                if (s.SETTINGS['enhance1']):
                    phi = 1
                    theta = 1
                    eyearea = (maxVal / phi) * (eyearea / (maxVal / theta)) ** 0.5
                    eyearea = np.array(eyearea, dtype=np.uint8)

                if (s.SETTINGS['enhance2']):
                    ret, eyearea = cv2.threshold(eyearea, s.SETTINGS['e2_toZero_thresh'], 255, cv2.THRESH_TOZERO)
                    ret, eyearea = cv2.threshold(eyearea, s.SETTINGS['e2_trunc_thresh'], 255, cv2.THRESH_TRUNC)
                    eyearea = Tracker.adjust_gamma(eyearea, s.SETTINGS['gammaAdjust'])

                if (s.SETTINGS['autothreshold']):
                    zeros = np.count_nonzero(eyearea == 0)
                    if (zeros != 0):
                        autothres_divisor = (zeros / 2000)  # number of zeroed pixels, should be around 2000

                #if args["display"] > 0:
                eyearea_copy = eyearea.copy()

                if (s.SETTINGS['debug']):
                    print("Sucessfully extracted eye area")

            except Exception as e:
                if (s.SETTINGS['debug']):
                    print("Eye area extraction failed:")
                    print(str(e))

            try:
                if (s.SETTINGS['method'] == "flood"):
                    # step 1 - inpaint glint in eyearea image to remove highlights
                    ret, glintmask = cv2.threshold(eyearea, maxVal - 50, maxVal, cv2.THRESH_BINARY)
                    kernel = np.ones((3, 3), np.uint8)
                    glintmask = cv2.dilate(glintmask, kernel, iterations=1)
                    eyearea = cv2.inpaint(eyearea, glintmask, s.SETTINGS['inpaintRadius'], cv2.INPAINT_NS)

                    #if args["display"] > 0:
                    #    eyeinpaint = eyearea.copy()

                    # step 2 - canny edge detection on eyearea
                    eyearea = Tracker.auto_canny(eyearea, 0.44)
                    eye_after_canny = eyearea.copy()
                    kernel = np.ones((3, 3), np.uint8)
                    # eyearea = cv2.dilate(eyearea, kernel, iterations=2)
                    eyearea_flood = eyearea.copy()

                    #if args["display"] > 0:
                    #    eyearea_preflood = eyearea.copy()

                    # step 3 - prepare mask used for flood fill
                    h, w = eyearea.shape[:2]
                    mask = np.zeros((h + 2, w + 2), np.uint8)

                    # step 4 - floodfill from point (0, 0)
                    cv2.floodFill(eyearea_flood, mask, (w - 1, h - 1), 255);

                    # step 5 - invert floodfilled image
                    ea_floodfill_inv = cv2.bitwise_not(eyearea_flood)

                    # step 6 - combine the two images to get the foreground.
                    eyearea = eyearea | ea_floodfill_inv

                elif (s.SETTINGS['method'] == "threshold"):
                    try:
                        ret, eyearea = cv2.threshold(eyearea, 1, 255, cv2.THRESH_BINARY)

                        #if args["display"] > 0:
                        #    eyeinpaint = eyearea.copy()
                    except Exception as e:
                        if (s.SETTINGS['debug']):
                            print("Thresholding failed:")
                            print(str(e))

                # step 7 - find contours
                cnts2 = []
                (_, cnts, hierarchy) = cv2.findContours(eyearea, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
                # cnts = sorted(cnts, key = cv2.contourArea, reverse = True)
                ratedCnts = []

                # loop over our contours for filtering
                hs, ws = eyearea.shape[:2]
                for c in cnts:

                    if (len(c) < 5):
                        continue

                    x, y, w, h = cv2.boundingRect(c)

                    if (w == 0 or h == 0):
                        continue

                    # if (float(w)/h > 2 or float(w)/h < 0.5):
                    # continue

                    area = cv2.contourArea(c)
                    # print("Area "+str(area))

                    if (area < 400 or area > 20000):
                        continue

                    '''
                    cmask = np.zeros(eyearea.shape,np.uint8)
                    cv2.drawContours(cmask,[c],0,255,-1)
                    mean_val = cv2.mean(eyearea, mask = cmask)

                    #print("Mean "+str(mean_val))
                    if(mean_val[0] > 100):
                        continue

                    #cnts2.append(c)
                    '''
                    ratedCnts.append(RatedContour(c, ws, hs, eyearea_src))

                ratedCnts = sorted(ratedCnts, key=lambda x: x.rating, reverse=True)

                # easy approach
                try:
                    ellipse = ratedCnts[0].ellipse
                except:
                    blink = True
                    if (s.SETTINGS['debug']):
                        print("No ellipse fitting possible")

                # push data to socket srv
                outdata = {}
                # outglint =
                if (blink):
                    outdata["center"] = (0.0, 0.0)
                    outdata["size"] = (0.0, 0.0)
                    outdata["glint"] = maxLoc
                    outdata["xoffs"] = (s.SETTINGS['xOffLeft'], s.SETTINGS['xOffRight'])
                    outdata["yoffs"] = (s.SETTINGS['yOffTop'], s.SETTINGS['yOffBot'])
                    outdata["blink"] = blink
                    outdata["confidence"] = 0.0
                    outdata["heartbpm"] = 0.0

                elif (ellipse != None):
                    # filter

                    if (s.SETTINGS['filtering']):
                        ellipseX = pupilFilterX(ellipse[0][0], int(round(time.time() * 1000)))
                        ellipseY = pupilFilterY(ellipse[0][1], int(round(time.time() * 1000)))
                        ellipseH = pupilFilterH(ellipse[1][0], int(round(time.time() * 1000)))
                        ellipseW = pupilFilterW(ellipse[1][1], int(round(time.time() * 1000)))
                    else:
                        ellipseX = ellipse[0][0]
                        ellipseY = ellipse[0][1]
                        ellipseH = ellipse[1][0]
                        ellipseW = ellipse[1][1]

                    outdata["center"] = (ellipseX, ellipseY)
                    outdata["size"] = (ellipseH, ellipseW)
                    outdata["glint"] = maxLoc
                    outdata["xoffs"] = (xOffLeft, xOffRight)
                    outdata["yoffs"] = (yOffTop, yOffBot)
                    outdata["blink"] = blink
                    outdata["confidence"] = float(ratedCnts[0].rating)
                    outdata["heartbpm"] = bpmFilter(self.processor.bpm.item(), int(round(time.time() * 1000)))

                s.OUT_TRACKDATA = outdata
            except Exception as e:
                s.OUT_TRACKDATA = {}
                s.logAppend(str(e))

                if (s.SETTINGS['debug']):
                    print("Analyze frame fail")
                    print(str(e))


            # prepare processed image for web display
            try:
                h, w = eyearea_copy.shape[:2]
                dst = np.zeros((h, w, 3), np.uint8)

                # draw pupil ellipse
                cv2.ellipse(dst, ellipse, (0, 255, 0), 1)

                # draw pupil center marker
                cv2.circle(dst, (int(ellipse[0][0]), int(ellipse[0][1])), 3, (255, 255, 0), 1)

                # draw glint in eyeframe
                cv2.circle(dst, ((xOffLeft * -1) -2, (yOffTop * -1)-2), 5, (255, 0, 255), 1)

                eyearea_copy = cv2.cvtColor(eyearea_copy, cv2.COLOR_GRAY2BGR)
                eyearea_copy = cv2.addWeighted(eyearea_copy, 0.7, dst, 0.3, 0)

                s.OUT_IMGPROC = eyearea_copy.copy()
                s.OUT_IMGRAW = self.processor.frame_out.copy()
            except:
                if(s.SETTINGS['debug']):
                    print("procimg fail")
                    s.OUT_IMGPROC = gray.copy()

            # ws_app.wsSend(jsonpickle.encode(cnts2))

            # check to see if the frame should be displayed to our screen
            '''try:
                # draw glint in full frame
                cv2.circle(frame, maxLoc, 5, (255, 220, 255), 1)
            except:
                # nothing
                if (s.SETTINGS['debug']):
                    print("disp glint frame err")
            try:
                h, w = eyearea_copy.shape[:2]
                dst = np.zeros((h, w, 3), np.uint8)

                # draw pupil ellipse
                cv2.ellipse(dst, ellipse, (0, 255, 0), 1)

                # draw pupil center marker
                cv2.circle(dst, (int(ellipse[0][0]), int(ellipse[0][1])), 3, (255, 255, 0), 1)

                # draw glint in eyeframe
                cv2.circle(dst, (yOffTop * -1, xOffLeft * -1), 5, (255, 0, 255), 1)

                eyearea_copy = cv2.cvtColor(eyearea_copy, cv2.COLOR_GRAY2BGR)
                eyearea_copy = cv2.addWeighted(eyearea_copy, 0.7, dst, 0.3, 0)

                s.OUT_IMGPROC = eyearea_copy.copy()

            # cv2.imshow("DST", dst)
            except:
                # nothing
                if (s.SETTINGS['debug']):
                    print("disp dst superimpose err")
            try:
                cv2.imshow("EyePreflood", eyearea)
                # cv2.imshow("GrayInpaint", gray)
                cv2.imshow("EyeCopy", eyearea_copy)
            except:
                if (s.SETTINGS['debug']):
                    print("proc disp err")
            if (SHOW_ALL):
                try:
                    cv2.imshow("EyeFlood", eyearea_flood)
                    cv2.imshow("EyeCanny", eye_after_canny)
                except:
                    # nothing
                    if (s.SETTINGS['debug']):
                        print("track disp err")

                try:
                    cv2.imshow("EyeInpaint", eyeinpaint)
                    cv2.imshow("InPaintMask", glintmask)
                except:
                    if (s.SETTINGS['debug']):
                        print("src disp err")

                # try:
                if (len(cnts) > 0):
                    cv2.drawContours(frame, cnts, -1, (0, 0, 255), 1)  # , offset=(maxLoc[0]-80,maxLoc[1]-80))
                if (len(cnts2) > 0):
                    cv2.drawContours(frame, cnts2, -1, (0, 255, 0), 1)  # , offset=(maxLoc[0]-80,maxLoc[1]-80))
                if (len(ratedCnts) > 0):
                    font = cv2.FONT_HERSHEY_SIMPLEX
                    for c in ratedCnts:
                        cv2.drawContours(frame, [c.contour], -1, (c.ratingAsColor, 0, 0),
                                         2)  # , offset=(maxLoc[0]-80,maxLoc[1]-80))
                        cv2.putText(frame, str(c.rating), (c.x, c.y), font, 0.4, (255, 255, 255), 1)
                        # cv2.putText(frame,str(c.circRating),(c.x, c.y+8), font, 0.4,(255,255,255),1)
                        cv2.circle(frame, (c.cx, c.cy), 3, (255, 120, 255), 1)
                # except:
                if (s.SETTINGS['debug']):
                    print("draw contours err")

                cv2.imshow("Frame", frame)

            # cv2.imshow("Thresh", thresh)
            # cv2.imshow("ThreshInv", grayinv)
            # update the FPS counter
            fps.update()
            # print("Frame!")'''