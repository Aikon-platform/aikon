function refToIIIF(imgRef){
    imgRef = imgRef.split("_");
    const imgCoord = imgRef.pop().replace(".jpg", "");
    const imgName = imgRef.join("_");
    return `${CANTALOUPE_APP_URL}/iiif/2/${imgName}.jpg/${imgCoord}/full/0/default.jpg`;
}

function refToMirador(imgRef){
    imgRef = imgRef.split("_");
    const digitRef = `${imgRef[0]}_${imgRef[1]}`;
    const annoRef = annoRefs.filter(ref => ref.startsWith(digitRef))[0]
    const manifest = `${APP_URL}/${APP_NAME}/iiif/${MANIFEST_V2}/${annoRef}/manifest.json`
    return `${SAS_APP_URL}/index.html?iiif-content=${manifest}&canvas=${parseInt(imgRef[2])}`
}

function getCheckedRefs(checked_ref) {
    let checkedAnnoRefs = [];
    checkedAnnoRefs.push(checked_ref)
    const options = document.querySelectorAll('#multi-select option:checked');

    options.forEach(function(option) {
        checkedAnnoRefs.push(option.id);
    });

    return checkedAnnoRefs;
}

const displayScores = (scores) => {
    const table = document.getElementById("similarity");
    table.innerHTML = "";
    const queryImgs = Object.keys(scores);

    if (queryImgs.length > 0) {
        queryImgs.map(qImg => {
            const similarities = scores[qImg];
            const row = table.insertRow();
            row.innerHTML = `<th>
                <a href="${refToMirador(qImg)}" target="_blank">
                    <img class="anno-img" src='${refToIIIF(qImg)}' alt="Annotation ${qImg}" title="${qImg}">
                    <h3>${qImg}</h3>
                </a>
            </th>`;

            if (similarities && similarities.length){
                similarities.map(similarity => {
                    let [score, sImg] = similarity;
                    const sCell = row.insertCell();
                    sCell.innerHTML = `
                        <a href="${refToMirador(sImg)}" target="_blank">
                            <img class="anno-img" src='${refToIIIF(sImg)}' alt="Annotation ${sImg}" title="${sImg}">
                            <h4>${sImg}</h4>
                        </a>`;
                    });
            }
        })
    } else {
        const emptyRow = table.insertRow();
        const cell = emptyRow.insertCell(0);
        cell.innerHTML = APP_LANG === "en" ? `Similarity scores were not computed for these ${WIT}es` :
            `Les scores de similarité n'ont pas été calculés pour ces ${WIT}s`;
    }
}

function sendScoreRequest(annoRefs, maxRows=20, showCheckedRef=false) {
    fetch(`${APP_URL}/${APP_NAME}/compute-score`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            "X-CSRFToken": CSRF_TOKEN
        },
        body: JSON.stringify({ annoRefs: annoRefs, maxRows: maxRows, showCheckedRef: showCheckedRef }),
    })
    .then(response => response.json()) // This line is needed to parse the response as JSON
    .then(score => {
        displayScores(score);
    })
    .catch(error => {
        console.error('Error sending data to the server:', error);
    });
}
