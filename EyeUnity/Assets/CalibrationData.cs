using UnityEngine;
using System.Collections;
using System.Collections.Generic;

public class CalibrationData {

	public Vector2 medianVector;
	public Vector2 point;
	public float distance;

	public CalibrationData(Vector2 point, List<Vector2> vectors){
		medianVector = calcMedianPoint (point, vectors);
		this.point = point;
	}

	private Vector2 calcMedianPoint(Vector2 reference, List<Vector2> scores){
		Vector2 median;
		List<Vector2> sortedScores = SortByDistance(reference, scores);
		if(sortedScores.Count % 2 == 0){
			median = (sortedScores [sortedScores.Count / 2] + sortedScores [sortedScores.Count / 2 - 1]) / 2;
		}else{
			median = sortedScores [sortedScores.Count / 2];
		}


		return median;
	}

	private List<Vector2> SortByDistance(Vector2 reference, List<Vector2> scores){
		return scores;
		Dictionary<float, int> distanceAndId = new Dictionary<float, int> ();
		List<Vector2> sortedList = new List<Vector2> ();
		for (int i = 0; i < scores.Count; i++) {
			float dist = (reference - scores [i]).magnitude;

			while(distanceAndId.ContainsKey(dist))
				dist+=0.00000001f;

			distanceAndId.Add (dist, i);
		}
		int last = sortedList.Count;
		while (sortedList.Count < scores.Count && sortedList.Count != last) {
			float min = 100000000;
			int leastId = -1;
			last = sortedList.Count;

			foreach(KeyValuePair<float, int> re in distanceAndId){
				if (re.Key > min)
					continue;
				leastId = re.Value;
				min = re.Key;
			}
			sortedList.Add (scores [leastId]);
			distanceAndId.Remove (min);
		}

		return sortedList;
	}

}
