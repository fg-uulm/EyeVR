using UnityEngine;
using System.Collections;
using System.Collections.Generic;
using MathNet.Numerics.LinearAlgebra;
//using MathNet.Numerics.LinearAlgebra.Single.Solvers;

public class Calibration {

	public List<CalibrationData> calibrationData;
	private MathNet.Numerics.LinearAlgebra.Matrix coefficientsX;
	private MathNet.Numerics.LinearAlgebra.Matrix coefficientsY;

//	MathNet.Numerics.LinearAlgebra.Matrix<float> coefficientsX;
//	MathNet.Numerics.LinearAlgebra.Matrix<float> coefficientsY;
	public bool Calibrate(int accuracyThreshold, int maxExceedence) {
		
		// Calculate the coordinate
		calcCoefficients();
//		LOG_D(" Calibration actual point: " << calibrationData.at(0).getActualPoint()
//			<< " Measured point " << calcCoordinates(calibrationData.at(0).getMeasuredMedianVector()));

		calcCalibrationDataDistance();

//		LOG_D("Average deviation: " << calcAverageDeviation());

		int errors = 0;
		// Check how many distances are greater than threshold and remove them   

		for(int i = 0; i < calibrationData.Count; i++){
			CalibrationData it = calibrationData [i];
			if (it.distance > accuracyThreshold){
				calibrationData.Remove (it);
				errors++;
				i--;
			}
		}
			
		// If the calibration process is not accurate enough, false will be returned
		if (errors > maxExceedence)
			return false;

		// Otherwise consider only those measurements smaller than threshold
		calcCoefficients();

		return true;
	}



	void calcCoefficients() {
		int matSize = calibrationData.Count;
		Debug.Log (matSize);
		if (matSize == 0) {
			//throw WrongArgumentException("Cannot calculate coeffizients with matSize=0!");
		}
	//	MathNet.Numerics.LinearAlgebra.Matrix<float> 
		double [,] m = new double[matSize,4];
		double [,] m2 = new double[matSize,1];

		MathNet.Numerics.LinearAlgebra.Matrix measurementsX = MathNet.Numerics.LinearAlgebra.Matrix.Create(m);
		MathNet.Numerics.LinearAlgebra.Matrix measurementsY = MathNet.Numerics.LinearAlgebra.Matrix.Create(m);

		MathNet.Numerics.LinearAlgebra.Matrix calibrationPointX = MathNet.Numerics.LinearAlgebra.Matrix.Create(m2);
		MathNet.Numerics.LinearAlgebra.Matrix calibrationPointY = MathNet.Numerics.LinearAlgebra.Matrix.Create(m2);


//		MathNet.Numerics.LinearAlgebra.Matrix<float> measurementsX = MathNet.Numerics.LinearAlgebra.Matrix<float>.Build.Dense(matSize, 4);			
//		MathNet.Numerics.LinearAlgebra.Matrix<float> measurementsY = MathNet.Numerics.LinearAlgebra.Matrix<float>.Build.Dense(matSize, 4);

//		Matrix<float> calibrationPointX = Matrix<float>.Build.Dense(1, matSize);
//		Matrix<float> calibrationPointY = Matrix<float>.Build.Dense(1, matSize);


		// Iterate over all calibration data
		for (int it = 0; it < matSize; it++) {

			double x = (calibrationData[it].medianVector.x);
			double y = calibrationData[it].medianVector.y;

			// Formaula from "Eye Gaze Tracking under natural head movements"
			measurementsX[it, 0] = 1;
			measurementsX[it, 1] = x;
			measurementsX[it, 2] = y;
			measurementsX[it, 3] = x * y;

			measurementsY[it, 0] = 1;
			measurementsY[it, 1] = x;
			measurementsY[it, 2] = y;
			measurementsY[it, 3] = x * y;

			calibrationPointX[it,0] = calibrationData[it].point.x;
			calibrationPointY[it,0] = calibrationData[it].point.y;
		}
	//	SingularValueDecomposition svd = measurementsX.SingularValueDecomposition;
		//coefficientsX = measurementsX.QRDecomposition.Solve(calibrationPointX);
		//coefficientsY = measurementsY.QRDecomposition.Solve (calibrationPointY);
		//	coefficientsX = measurementsX.CholeskyDecomposition.Solve(calibrationPointX);
	//	coefficientsY = measurementsY.CholeskyDecomposition.Solve(calibrationPointY);
		coefficientsX = measurementsX.LUDecomposition.Solve (calibrationPointX);
		coefficientsY = measurementsX.LUDecomposition.Solve (calibrationPointY);

		Debug.Log (coefficientsX);
		Debug.Log (coefficientsY);

		//System.IO.File.WriteAllText("calibDatacoffX.txt", coefficientsX.ToString());

		//System.IO.File.WriteAllText("calibDatacoffY.txt", coefficientsY.ToString());
		//		
//		MathNet.Numerics.LinearAlgebra.Factorization.Svd<float> svd = measurementsX.Svd();
//		coefficientsX = svd.Solve (calibrationPointX);

//		MathNet.Numerics.LinearAlgebra.Factorization.Svd<float> svd2 = measurementsY.Svd();
//		coefficientsY = svd.Solve (calibrationPointY);
	}

	void calcCalibrationDataDistance(){
		for (int i = 0; i < calibrationData.Count; i++) {
			CalibrationData it = calibrationData [i];
			Vector2 calculatedPoint = CalcCoordinates (it.medianVector);
			Vector2 actualPoint = it.point;
			float distance = calcPointDistance (actualPoint, calculatedPoint);

			it.distance = distance;
		}
	}

	public Vector2 CalcCoordinates(Vector2 vector){
		/*float a0 = (float)coefficientsX[0, 0];
		float a1 = (float)coefficientsX[0, 1];
		float a2 = (float)coefficientsX[0, 2];
		float a3 = (float)coefficientsX[0, 3];

		float b0 = (float)coefficientsY[0, 0];
		float b1 = (float)coefficientsY[0, 1];
		float b2 = (float)coefficientsY[0, 2];
		float b3 = (float)coefficientsY[0, 3];*/

		float a0 = (float)coefficientsX[0, 0];
		float a1 = (float)coefficientsX[1, 0];
		float a2 = (float)coefficientsX[2, 0];
		float a3 = (float)coefficientsX[3, 0];


		float b0 = (float)coefficientsY[0, 0];
		float b1 = (float)coefficientsY[1, 0];
		float b2 = (float)coefficientsY[2, 0];
		float b3 = (float)coefficientsY[3, 0];

		//Debug.Log("A: " +a0+", "+a1 + ", " +a2+", "+a3);
		//Debug.Log("B: " +b0+", "+b1 + ", " +b2+", "+b3);

		float x = (a0 + a1 * vector.x + a2 * vector.y + a3 * vector.x * vector.y);
		float y = (b0 + b1 * vector.x + b2 * vector.y + b3 * vector.x * vector.y);
		 
		return new Vector2(x,y);
	}

	private float calcPointDistance(Vector2 v1, Vector2 v2){
		return (v1 - v2).magnitude;
	}

}
