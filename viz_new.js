d = document; // get elements & start by retrieving the subject:
wl = window.location;
proc = d.getElementById("procsel");
proc.value = wl.search.substr(5) == "" ? "1" : wl.search.substr(5);
proc.oninput = function (e) {
	wl.href = "index_new.html?prc=" + proc.value;
};

function loadScript(url, callback) {
	var script = d.createElement("script");
	script.type = "text/javascript";
	script.src = url;
	script.onreadystatechange = callback;
	script.onload = callback;
	d.head.appendChild(script);
}

var plotData = function () {
	const ids = [...Array(bendDieLatT.length).keys()];
	const bendData = [
		ids,
		bendDieLatT,
		bendDieRotT,
		bendDieVerT,
		bendDieLatM,
		bendDieRotA,
		bendDieVerM,
		colletAxT,
		colletRotT,
		colletAxMov,
		colletRotMov,
		mandrelAxLoad,
		mandrelAxMov,
		pressAxT,
		pressLatT,
		pressLeftAxT,
		pressAxMov,
		pressLatMov,
		pressLeftAxMov,
		clampLatT,
		clampLatMov,
	];
	let uSync = uPlot.sync("both");
	// wheel scroll zoom
	const wheelZoomHk = [
		(u) => {
			let rect = u.over.getBoundingClientRect();
			u.over.addEventListener(
				"wheel",
				(e) => {
					let oxRange = u.scales.x.max - u.scales.x.min;
					let nxRange = e.deltaY < 0 ? oxRange * 0.95 : oxRange / 0.95;
					let nxMin =
						u.posToVal(u.cursor.left, "x") -
						(u.cursor.left / rect.width) * nxRange;
					if (nxMin < 0) nxMin = 0;
					let nxMax = nxMin + nxRange;
					if (nxMax > u.data[0][u.data[0].length - 1])
						nxMax = u.data[0][u.data[0].length - 1];
					u.batch(() => {
						uPlot.sync(u.cursor.sync.key).plots.forEach((p) => {
							p.setScale("x", { min: nxMin, max: nxMax });
						});
					});
				},
				{ passive: true },
			);
		},
	];

	const cursorOpts = {
		lock: true,
		sync: { key: "a" },
		y: false,
	};
	let opts = {
		width: window.innerWidth,
		height: window.innerHeight - 90,
		cursor: cursorOpts,
		axes: [{}, { scale: "readings", side: 1, grid: { show: true } }],
		scales: { auto: false, x: { time: false } },
		legend: { show: false },
	};
	const drawHkBend = [
		(u) => {
			u.ctx.textAlign = "left";
			u.ctx.fillStyle = "black";
			tpos = u.valToPos(bendDieLatT[0], "y", true);
			u.ctx.fillText("Bend Die", 2, tpos - 90);
			u.ctx.fillStyle = "red";
			u.ctx.fillText("Lateral Torque", 7, tpos - 60);
			u.ctx.fillStyle = "green";
			u.ctx.fillText("Rotating Torque", 7, tpos - 30);
			u.ctx.fillStyle = "blue";
			u.ctx.fillText("Vertical Torque", 7, tpos);
			u.ctx.fillStyle = "purple";
			u.ctx.fillText("Lateral Movement", 7, tpos + 30);
			u.ctx.fillStyle = "grey";
			u.ctx.fillText("Rotating Angle", 7, tpos + 60);
			u.ctx.fillStyle = "brown";
			u.ctx.fillText("Vertical Movement", 7, tpos + 90);

			u.ctx.fillStyle = "black";
			tpos = u.valToPos(colletRotMov[0], "y", true);
			u.ctx.fillText("Collet", 2, tpos - 60);
			u.ctx.fillStyle = "red";
			u.ctx.fillText("Axial Torque", 7, tpos - 30);
			u.ctx.fillStyle = "green";
			u.ctx.fillText("Rotating Torque", 7, tpos);
			u.ctx.fillStyle = "blue";
			u.ctx.fillText("Axial Movement", 7, tpos + 30);
			u.ctx.fillStyle = "purple";
			u.ctx.fillText("Rotating Movement", 7, tpos + 60);

			tpos = u.valToPos(mandrelAxLoad[0], "y", true);
			u.ctx.fillStyle = "black";
			u.ctx.fillText("Mandrel", 2, tpos - 30);
			u.ctx.fillStyle = "red";
			u.ctx.fillText("Axial Load", 7, tpos);
			u.ctx.fillStyle = "green";
			u.ctx.fillText("Axial Movement", 7, tpos + 30);

			tpos = u.valToPos(pressAxT[0], "y", true);
			u.ctx.fillStyle = "black";
			u.ctx.fillText("Pressure Die", 2, tpos - 60);
			u.ctx.fillStyle = "red";
			u.ctx.fillText("Axial Torque", 7, tpos - 30);
			u.ctx.fillStyle = "green";
			u.ctx.fillText("Lateral Torque", 7, tpos);
			u.ctx.fillStyle = "blue";
			u.ctx.fillText("Left Axial Torque", 7, tpos + 30);
			u.ctx.fillStyle = "purple";
			u.ctx.fillText("Axial Movement", 7, tpos + 60);
			u.ctx.fillStyle = "grey";
			u.ctx.fillText("Lateral Movement", 7, tpos + 90);
			u.ctx.fillStyle = "brown";
			u.ctx.fillText("Left Axial Movement", 7, tpos + 120);

			tpos = u.valToPos(clampLatT[0], "y", true);
			u.ctx.fillStyle = "black";
			u.ctx.fillText("Clamp Die", 2, tpos - 30);
			u.ctx.fillStyle = "red";
			u.ctx.fillText("Lateral Torque", 7, tpos);
			u.ctx.fillStyle = "green";
			u.ctx.fillText("Lateral Movement", 7, tpos + 30);
		},
	];
	let bendOpts = {
		id: "bendChart",
		series: [
			{ fill: false, ticks: { show: false } },
			{ label: "bendDieLatT", stroke: "red" },
			{ label: "bendDieRotT", stroke: "green" },
			{ label: "bendDieVerT", stroke: "blue" },
			{ label: "bendDieLatM", stroke: "purple" },
			{ label: "bendDieRotA", stroke: "grey" },
			{ label: "bendDieVerM", stroke: "brown" },
			{ label: "colletAxT", stroke: "red" },
			{ label: "colletRotT", stroke: "green" },
			{ label: "colletAxMov", stroke: "blue" },
			{ label: "colletRotMov", stroke: "purple" },
			{ label: "mandrelAxLoad", stroke: "red" },
			{ label: "mandrelAxMov", stroke: "green" },
			{ label: "pressAxT", stroke: "red" },
			{ label: "pressLat", stroke: "green" },
			{ label: "pressLeftAxT", stroke: "blue" },
			{ label: "pressAxMov", stroke: "purple" },
			{ label: "pressLatMov", stroke: "grey" },
			{ label: "pressLeftAxMov", stroke: "brown" },
			{ label: "clampLatT", stroke: "red" },
			{ label: "clampLatMov", stroke: "green" },
		],
		hooks: { draw: drawHkBend, ready: wheelZoomHk },
	};
	bendOpts = Object.assign(opts, bendOpts);
	let bendPlot = new uPlot(bendOpts, bendData, document.body);

	cursorOverride = d.getElementsByClassName("u-cursor-x");
	for (i of [0]) cursorOverride[i].style = "border-right:3px solid #FF2D7D;";

	for (id of ["bendChart"]) d.getElementById(id).style.border = "solid";
	d.body.appendChild(
		d
			.createElement("p")
			.appendChild(
				d.createTextNode(
					"Scroll wheel zooms in and out, double-click resets the plot, click&drag zooms to a segment.",
				),
			),
	);

	// add info material:
	d.getElementById("infotext").innerHTML = info;

	// allow dynamic resizing:
	function getSize() {
		return { width: window.innerWidth, height: window.innerHeight - 100 };
	}
	window.addEventListener("resize", (e) => {
		bendPlot.setSize(getSize());
	});
};

loadScript("dta" + proc.value + ".js", plotData);
