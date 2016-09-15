/**
 * Created by fg on 08.08.16.
 */
var arrow = [
    [ 2, 0 ],
    [ -10, -4 ],
    [ -10, 4]
];

function drawFilledPolygon(shape) {
    ctx.beginPath();
    ctx.moveTo(shape[0][0],shape[0][1]);

    for(p in shape)
        if (p > 0) ctx.lineTo(shape[p][0],shape[p][1]);

    ctx.lineTo(shape[0][0],shape[0][1]);
    ctx.fill();
};

function translateShape(shape,x,y) {
    var rv = [];
    for(p in shape)
        rv.push([ shape[p][0] + x, shape[p][1] + y ]);
    return rv;
};

function rotateShape(shape,ang)
{
    var rv = [];
    for(p in shape)
        rv.push(rotatePoint(ang,shape[p][0],shape[p][1]));
    return rv;
};
function rotatePoint(ang,x,y) {
    return [
        (x * Math.cos(ang)) - (y * Math.sin(ang)),
        (x * Math.sin(ang)) + (y * Math.cos(ang))
    ];
};

function drawLineArrow(x1,y1,x2,y2) {
    ctx.beginPath();
    ctx.moveTo(x1,y1);
    ctx.lineTo(x2,y2);
    ctx.stroke();
    var ang = Math.atan2(y2-y1,x2-x1);
    drawFilledPolygon(translateShape(rotateShape(arrow,ang),x2,y2));
};

var canvas,ctx;
var cw = 600, ch = 400, na = 35;


function initArrows() {
    canvas = document.getElementById('drawing');
    ctx = canvas.getContext('2d');
	document.getElementById('redraw').onclick = randomLines;
    randomLines();
};

function randomLines()
{
    ctx.clearRect(0,0,cw,ch);
    for(i = 0; i < na; i++)
        drawLineArrow(
            Math.random() * cw, Math.random() * ch,
            Math.random() * cw, Math.random() * ch
        );
    return false;
};

window.onload = initArrows;