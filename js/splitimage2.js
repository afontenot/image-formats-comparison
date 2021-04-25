let container = document.getElementById("comparison");
let left = new Image();
let right = new Image();
let leftImSize = 1;
let rightImSize = 1;
let toggleMode = false;
let toggleImage = "right";
let split = 0.5;
let canvas, ctx;

const options = {
    file: document.getElementById('fileSel'), 
    scale: document.getElementById('scaleSel'),
    left: document.getElementById('leftSel'), 
    right: document.getElementById('rightSel'),
    subset: document.getElementById('subsetSel')
};

const header = document.getElementById("center-head");

let viewOptions = {
    file: '', 
    scale: '',
    left: '', 
    leftQ: '',
    right: '', 
    rightQ: ''
};

let urlFolder, urlFile;

options.file.onchange = function () {
    setFile();
};

options.left.onchange = function () {
    setSide('left');
};
options.right.onchange = function () {
    setSide('right');
};

leftQual.onchange = function () {
    setSide('left');
};
rightQual.onchange = function () {
    setSide('right');
};

// get the selected value from a selection element (like <option>)
function getSelValue(el, attr) {
    return el.options[el.selectedIndex].getAttribute(attr);
}

/* Get web-friendly string */
function getSlugName(str) {
    str = str.replace(/^\s+|\s+$/g, ''); // trim
    str = str.toLowerCase();

    // remove accents, swap ñ for n, etc
    var from = "ãàáäâẽèéëêìíïîõòóöôùúüûñç·/_,:;";
    var to = "aaaaaeeeeeiiiiooooouuuunc------";
    for (var i = 0, l = from.length; i < l; i++) {
        str = str.replace(new RegExp(from.charAt(i), 'g'), to.charAt(i));
    }

    str = str.replace(/[^a-z0-9 -]/g, '') // remove invalid chars
        .replace(/\s+/g, '-') // collapse whitespace and replace by -
        .replace(/-+/g, '-'); // collapse dashes

    return str;
}

function updateImagesOnCanvas() {
    let scaleVal = getSelValue(scaleSel, 'value');
    // disable image smoothing for clean double / triple enlargement
    ctx.imageSmoothingEnabled = false;
    ctx.drawImage(right, 0, 0, left.width, left.height, 0, 0, left.width * scaleVal, left.height * scaleVal);
    ctx.drawImage(left, 0, 0, split * left.width, left.height, 0, 0, split * left.width * scaleVal, left.height * scaleVal);
    if (!toggleMode) {
        ctx.lineWidth = 0.5;
        ctx.strokeStyle = 'white';
        ctx.setLineDash([2, 2]);
        ctx.beginPath();
        ctx.moveTo(split * canvas.width, 0);
        ctx.lineTo(split * canvas.width, canvas.height);
        ctx.stroke();
    }
}

function moveSplit(ev) {
    if (toggleMode) {
        return
    }
    split = ev.offsetX / canvas.width;
    updateImagesOnCanvas();
}

function canvasTouch(ev) {
    if (toggleMode) {
        toggleMode = false;
        updateInfoBox();
    }
    moveSplit(ev);
}

/* Spacebar to enter 'flip-view'. Repeat to flip between images. Any other key (or mouse click) to return to split-view. */
function switchMode(event) {
    if (event.keyCode) {
        if (event.keyCode == "32") {
            event.preventDefault();
            toggleMode = true;
            if (toggleImage == "left") {
                toggleImage = "right";
                split = 0;
            } else {
                toggleImage = "left";
                split = 1;
            }
        } else {
            toggleMode = false;
        }
        updateImagesOnCanvas();
        updateInfoBox();
    } 
}

function updateCanvas() {
    if (!canvas) {
        canvas = document.createElement('canvas');
        container.appendChild(canvas);
        canvas.addEventListener("mousemove", moveSplit, false);
        canvas.addEventListener("click", canvasTouch, false);
        ctx = canvas.getContext('2d');
        // add binding for <space> key to toggle image
        window.addEventListener("keydown", function (event) {
            switchMode(event);
        }, false);
    }
    let scaleVal = getSelValue(scaleSel, 'value');
    canvas.width = left.width * scaleVal;
    canvas.height = left.height * scaleVal;
    container.style.width = left.width * scaleVal + "px";
    container.style.height = left.height * scaleVal + "px";
    updateImagesOnCanvas();
    window.location.hash = (viewOptions.file).concat(viewOptions.scale,
        '&', viewOptions.left, '=', viewOptions.leftQ,
        '&', viewOptions.right, '=', viewOptions.rightQ);
}

function updateInfoBox() {
    header.innerHTML = "";
    let area = left.width * left.height;
    if (toggleMode) {
        if (toggleImage == "left") {
            header.innerHTML = getSelValue(options["left"], "folder") + " " + (leftImSize / 1000).toFixed(1) + " KB<br>" + (leftImSize * 8 / area).toFixed(2) + " bpp";
        } else {
            header.innerHTML = getSelValue(options["right"], "folder") + " " + (rightImSize / 1000).toFixed(1) + " KB<br>" + (rightImSize * 8 / area).toFixed(2) + " bpp";
        }
        return
    }
    /* messy, but basically just manually puts together the info div
     * has to be this way since we reuse it for toggle mode */
    let info = document.createElement("div");
    info.style.display = "flex";
    let leftSideInfo = document.createElement("div");
    leftSideInfo.style.flex = 1;
    leftSideInfo.innerHTML = (leftImSize / 1000).toFixed(1) + " KB<br>" + (leftImSize * 8 / area).toFixed(2) + " bpp";
    info.appendChild(leftSideInfo);
    let midInfo = document.createElement("div");
    midInfo.style.flex = 0;
    midInfo.innerHTML = " vs. ";
    info.appendChild(midInfo);
    let rightSideInfo = document.createElement("div");
    rightSideInfo.style.flex = 1;
    rightSideInfo.innerHTML = (rightImSize / 1000).toFixed(1) + " KB<br>" + (rightImSize * 8 / area).toFixed(2) + " bpp";
    info.appendChild(rightSideInfo);
    header.appendChild(info);
}

function setImage(side, pathBase, codec) {
    let img = (side == "right") ? right : left;
    let path = urlFolder.concat(pathBase, '/', urlFile, '.', codec);
    
    let xhr = new XMLHttpRequest();

    xhr.open("GET", path, true);
    xhr.responseType = "arraybuffer";

    xhr.onload = function () {

        let mimeCodec = (codec == 'jxr') ? 'vnd.ms-photo' : codec;
        let blob = new Blob([xhr.response], {
            type: "image/" + mimeCodec
        });
        let blobPath = window.URL.createObjectURL(blob);

        img.onload = function () {
            let area = img.width * img.height;
            if (side == "right") {
                rightImSize = xhr.response.byteLength;
            } else {
                leftImSize = xhr.response.byteLength;
            }
            window.URL.revokeObjectURL(blobPath);
            updateCanvas();
            updateInfoBox();
        };
        img.onerror = function () {
            this.onerror=null;
            img.src = urlFolder.concat(pathBase, '/', urlFile, '.', 'png');
        };
        img.src = blobPath;
        
    };
    xhr.send();
}

function setSide(side) {
    let isRight = (side == 'right') ? 1 : 0;
    let whichQual = (isRight) ? rightQual : leftQual;
    let image = getSelValue(options[side], 'value');
    let pathBase = getSelValue(options[side], 'folder');

    let quality = '';
    if (pathBase != 'original') {
        whichQual.disabled = false;
        quality = whichQual.options[whichQual.selectedIndex].innerHTML.toLowerCase() + '/';
    } else {
        whichQual.disabled = true;
    }

    pathBase = quality + pathBase;
    viewOptions[side] = image;
    viewOptions[side + 'Q'] = getSelValue(whichQual, 'value');

    setImage(side.toLowerCase(), pathBase, image);
}

function setFile() {
    urlFile = getSelValue(options.file, 'value');

    /* Any view change will update hash. */
    viewOptions.file = getSlugName(options.file.options[options.file.selectedIndex].text);

    setSide('right');
    setSide('left');
}

/* Process URL hash for direct links. */
function getWindowsOptions() {
    if (window.location.hash) {
        let hashArr, ampArr, imgOpts, name, scale, leftOpts, rightOpts;

        hashArr = (location.hash).split('#', 3);

        ampArr = (hashArr.pop() + '&=' + '&=').split('&', 5);
        imgOpts = ampArr[0].split('*', 2);
        leftOpts = ampArr[1].split('=', 2);
        rightOpts = ampArr[2].split('=', 2);

        for (let opt, j = 0; opt = options.file.options[j]; j++) {
            if (getSlugName(opt.text) == imgOpts[0]) {
                options.file.selectedIndex = j;
                let z, s, q;

                if (imgOpts[1]) {
                    let z = document.querySelector('#scaleSel [ratio="' + imgOpts[1] + '"]');
                    if (z) { z.selected = true };
                }
                if (leftOpts) {
                    s = document.querySelector('#leftSel [value="' + leftOpts[0] + '"]');
                    if (s) { s.selected = true };
                    q = document.querySelector('#leftQual [value="' + leftOpts[1] + '"]');
                    if (q) { q.selected = true };
                }
                if (rightOpts) {
                    s = document.querySelector('#rightSel [value="' + rightOpts[0] + '"]');
                    if (s) { s.selected = true };
                    q = document.querySelector('#rightQual [value="' + rightOpts[1] + '"]');
                    if (q) { q.selected = true };
                }
                break;
            }
        };
    };
}

document.addEventListener("DOMContentLoaded", function () {
    fetch("comparisonfiles.json")
        .then(response => response.json())
        .then(function (json) {
            // subset
            const subsetSel = document.getElementById("subsetSel");

            const subsetChange = function (event) {
                if (!event) {
                    value = subsetSel.value;
                } else {
                    value = event.target.value;
                }
                // format
                const leftSel = document.getElementById("leftSel");
                const rightSel = document.getElementById("rightSel");
                while (leftSel.firstChild) {
                    leftSel.removeChild(leftSel.firstChild);
                }
                while (rightSel.firstChild) {
                    rightSel.removeChild(rightSel.firstChild);
                }
                for (let format of json["comparisonfiles"][value]["format"]) {
                    let optLeft = document.createElement("option");
                    let optRight = document.createElement("option");
                    optLeft.setAttribute("folder", format["name"]);
                    optLeft.text = format["name"];
                    optLeft.value = format["extension"];
                    leftSel.add(optLeft, null);
                    optRight.setAttribute("folder", format["name"]);
                    optRight.text = format["name"];
                    optRight.value = format["extension"];
                    rightSel.add(optRight, null);
                }
                // files
                let fileSel = document.getElementById("fileSel");
                while (fileSel.firstChild) {
                    fileSel.removeChild(fileSel.firstChild);
                }
                let filesList = json["comparisonfiles"][value]["files"]
                filesList.sort(function(a,b) {
                    if ( a.title < b.title )
                        return -1;
                    if ( a.title > b.title )
                        return 1;
                    return 0;
                })
                for (let file of filesList) {
                    let opt = document.createElement("option");
                    opt.value = file["filename"];
                    opt.text = file["title"];
                    fileSel.add(opt, null);
                }
                getWindowsOptions();
                urlFolder = "comparisonfiles/" + getSelValue(options.subset, 'value') + "/";
                setFile();
            }

            subsetSel.onchange = subsetChange;
            options.scale.onchange = updateCanvas;

            for (let subset in json['comparisonfiles']) {
                let opt = document.createElement("option");
                opt.value = subset;
                opt.text = subset;
                subsetSel.add(opt, null);
            }
            subsetChange();
            urlFolder = "comparisonfiles/" + getSelValue(options.subset, 'value') + "/";
            setFile();
        });
});
