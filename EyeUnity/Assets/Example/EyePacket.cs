using System;
using UnityEngine;
using System.Collections;
using System.Collections.Generic;
using System;
using Newtonsoft.Json;

internal class Glint
{
	[JsonProperty("py/tuple")]
	public List<float> PyTuple { get; set; }
	public Vector2 AsVector { 
		get {
			if (PyTuple.Count > 1)
				return new Vector2 (PyTuple [0], PyTuple [1]);
			else
				return new Vector2 ();
		}
	}
}

internal class Xoffs
{
	[JsonProperty("py/tuple")]
	public List<float> PyTuple { get; set; }
	public Vector2 AsVector { 
		get {
			if (PyTuple.Count > 1)
				return new Vector2 (PyTuple [0], PyTuple [1]);
			else
				return new Vector2 ();
		}
	}
}

internal class Yoffs
{
	[JsonProperty("py/tuple")]
	public List<float> PyTuple { get; set; }
	public Vector2 AsVector { 
		get {
			if (PyTuple.Count > 1)
				return new Vector2 (PyTuple [0], PyTuple [1]);
			else
				return new Vector2 ();
		}
	}
}

internal class Center
{
	[JsonProperty("py/tuple")]
	public List<float> PyTuple { get; set; }
	public Vector2 AsVector { 
		get {
			if (PyTuple.Count > 1)
				return new Vector2 (PyTuple [0], PyTuple [1]);
			else
				return new Vector2 ();
		}
	}
}

internal class Size
{
	[JsonProperty("py/tuple")]
	public List<float> PyTuple { get; set; }
	public Vector2 AsVector { 
		get {
			if (PyTuple.Count > 1)
				return new Vector2 (PyTuple [0], PyTuple [1]);
			else
				return new Vector2 ();
		}
	}
}

internal class EyeData
{

	[JsonProperty("glint")]
	public Glint Glint { get; set; }

	[JsonProperty("xoffs")]
	public Xoffs Xoffs { get; set; }

	[JsonProperty("yoffs")]
	public Yoffs Yoffs { get; set; }

	[JsonProperty("center")]
	public Center Center { get; set; }

	[JsonProperty("size")]
	public Size Size { get; set; }

	[JsonProperty("blink")]
	public bool Blink { get; set; }

	[JsonProperty("confidence")]
	public float Confidence { get; set; }

	public Vector2 CombinedOffset {
		get {
			return new Vector2 (Xoffs.AsVector.x, Yoffs.AsVector.x);
		}
	}
}

internal class EyePacket
{
	[JsonProperty("data")]
	public EyeData Data { get; set; }

	[JsonProperty("type")]
	public string Type { get; set; }
}