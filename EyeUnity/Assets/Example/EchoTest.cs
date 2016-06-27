using UnityEngine;
using System.Collections;
using System.Collections.Generic;
using System;
using Newtonsoft.Json;

public class EchoTest : MonoBehaviour {
	WebSocket w;
	OneEuroFilter fx;
	OneEuroFilter fy;
	OneEuroFilter fs;
	public bool isOffline = false;

	int frame = 0;
	List<Vector2> capture;
	// Use this for initialization
	IEnumerator Start () {
		WebSocket w = new WebSocket(new Uri("ws://134.60.70.23:8080/websocket"));
		//WebSocket w = new WebSocket(new Uri("ws://192.168.178.64:8080/websocket"));
		yield return StartCoroutine(w.Connect());
		//w.SendString("Hi there");
		int i=0;

		fx = new OneEuroFilter (2.0, 0.2);
		fy = new OneEuroFilter (2.0, 0.2);
		fs = new OneEuroFilter (15.0, 0.2);

		Transform pS = transform.Find ("pupilSphere");
		if (isOffline) {
			JsonSerializerSettings serSet = new JsonSerializerSettings ();		 
			serSet.ReferenceLoopHandling = ReferenceLoopHandling.Ignore;
			capture = JsonConvert.DeserializeObject<List<Vector2>>(System.IO.File.ReadAllText ("calibDataTL.txt"), serSet);
		}
		while (true)
		{
			if (isOffline && capture != null && capture.Count > 0) {
				frame++;
				if (frame >= capture.Count)
					frame = 0;
				EyeData ret = new EyeData ();
						if (CurrentCalibration != null) {
					Vector2 gazePos = CurrentCalibration.CalcCoordinates(capture[frame]);
							pS.localPosition = new Vector3 (gazePos.x, gazePos.y, 1.32f);
							//Debug.Log (gazePos);
						} 
					
				yield return 0;
			} else {
				string reply = w.RecvString ();
				if (reply != null) {
					//Debug.Log ("Received: "+reply);
					EyeData ret = JsonConvert.DeserializeObject<EyeData> (reply);
					if (ret.Size == null) {
						Debug.Log ("No pupil");
						pS.GetComponent<Renderer> ().material.color = Color.red;
						continue;
					} else {
						//Debug.Log(ret);
						//Debug.Log(ret.Glint.AsVector);
						float size = (float)fs.Filter (ret.Size.AsVector.y / 60, 30.0);
						//Debug.Log (size);
						pS.GetComponent<Renderer> ().material.color = Color.black;
						pS.localScale = new Vector3 (size, size, size);

						lastVector = ret.CombinedOffset - ret.Center.AsVector;

						if (CurrentCalibration != null) {
							Vector2 gazePos = CurrentCalibration.CalcCoordinates (lastVector);
							pS.localPosition = new Vector3 (gazePos.x, gazePos.y, 1.32f);
							//Debug.Log (gazePos);
						} else if (xRatio != 0) {
							Vector3 newPos = new Vector3 (0.0f, 0.0f, 1.32f);
							//newPos.x = (lastVector.x / xRatio) + xOffset;
							//newPos.y = (lastVector.y / yRatio) + yOffset;
							newPos.x = (float)fx.Filter ((lastVector.x - cx) / xRatio, 30.0);
							newPos.y = (float)fy.Filter ((lastVector.y - cy) / yRatio, 30.0);
							pS.localPosition = newPos;
							//Debug.Log ("New pos: " + newPos);
						} else {
							pS.GetComponent<Renderer> ().material.color = Color.gray;
							pS.localPosition = new Vector3 (0.0f, 0.0f, 2.32f);
						}
					}
				}
				if (w.error != null) {
					Debug.LogError ("Error: " + w.error);
					InvokeRepeating ("Reconnect", 5, 10.0F);
					break;
				} else {
					CancelInvoke ("Reconnect");
				}
				yield return 0;
			}
		}
		w.Close();
	}

	public Vector2 lastVector;

	public Calibration CurrentCalibration;

	public float xRatio = 0;
	public float yRatio;
	public float xOffset;
	public float yOffset;
	public float cx;
	public float cy;
}
