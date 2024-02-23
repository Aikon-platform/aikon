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

function getCheckedRefs() {
    let checkedAnnoRefs = [];
    const checkboxes = document.querySelectorAll('#check-pairs input[type="checkbox"]:checked');

    checkboxes.forEach(function(checkbox) {
        checkedAnnoRefs.push(checkbox.id);
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
                <img class="anno-img" src='${refToIIIF(qImg)}' alt="Annotation ${qImg}"><br>
                <h3><a href="${refToMirador(qImg)}" target="_blank">${qImg}</a></h3>
            </th>`;

            if (similarities && similarities.length){
                similarities.map(similarity => {
                    let [score, sImg] = similarity;
                    const sCell = row.insertCell();
                    sCell.innerHTML = `
                        <img class="anno-img" src='${refToIIIF(sImg)}' alt="Annotation ${sImg}"><br>
                        <h4><a href="${refToMirador(sImg)}" target="_blank">${sImg}</a><br><b>${score}</b></h4>`;
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

function sendScoreRequest(annoRefs) {
    fetch(`${APP_URL}/${APP_NAME}/compute-score`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            "X-CSRFToken": CSRF_TOKEN
        },
        body: JSON.stringify({ annoRefs: annoRefs }),
    })
    .then(response => {
        if (!response.ok) {
            throw new Error(`HTTP error! Status: ${response.status}`);
        }
        return response.json();
    })
    .then(data => {
        if (data && data.taskId) {
            checkStatus(data.taskId, displayScores);
        } else {
            console.error('Invalid server response. Missing taskId.');
        }
    })
    .catch(error => {
        console.error('Error sending data to the server:', error);
    });
}

document.addEventListener('DOMContentLoaded', function() {
    const checkboxes = document.querySelectorAll('#check-pairs input[type="checkbox"]');

    checkboxes.forEach(function(checkbox) {
        checkbox.addEventListener('change', function() {
            sendScoreRequest(getCheckedRefs());
        });
    });
    checkboxes[0].dispatchEvent(new Event('change'));
});
