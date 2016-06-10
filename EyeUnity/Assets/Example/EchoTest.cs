using UnityEngine;
using System.Collections;
using System;
using Newtonsoft.Json;

public class EchoTest : MonoBehaviour {
	WebSocket w;

	// Use this for initialization
	IEnumerator Start () {
		WebSocket w = new WebSocket(new Uri("ws://134.60.70.23:8080/websocket"));
		yield return StartCoroutine(w.Connect());
		//w.SendString("Hi there");
		int i=0;

		Transform pS = transform.Find ("pupilSphere");

		while (true)
		{
			string reply = w.RecvString();
			if (reply != null)
			{
				//Debug.Log ("Received: "+reply);
				EyeData ret = JsonConvert.DeserializeObject<EyeData>(reply);
				if (ret.Size == null) {
					Debug.Log ("No pupil");
					pS.GetComponent<Renderer>().material.color = Color.red;
					continue;
				} else {
					//Debug.Log(ret);
					//Debug.Log(ret.Glint.AsVector);
					float size = ret.Size.AsVector.y/40;
					//Debug.Log (size);
					pS.GetComponent<Renderer>().material.color = Color.black;
					pS.localScale = new Vector3(size, size, size);

					lastVector = ret.CombinedOffset - ret.Center.AsVector;

					if (CurrentCalibration != null) {
						Vector2 gazePos = CurrentCalibration.CalcCoordinates(lastVector);
						pS.localPosition = new Vector3 (gazePos.x, gazePos.y, 1.32f);
						Debug.Log (gazePos);
					} else if(xRatio != 0) {
						Vector3 newPos = new Vector3(0.0f, 0.0f, 1.32f);
						newPos.x = (lastVector.x + xOffset) * xRatio;
						newPos.y = (lastVector.y + yOffset) * yRatio;
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
		w.Close();
	}

	public Vector2 lastVector;

	public Calibration CurrentCalibration;

	public float xRatio = 0;
	public float yRatio;
	public float xOffset;
	public float yOffset;
}
