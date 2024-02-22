const csrfToken = $("input[name=csrfmiddlewaretoken]").val();
function checkStatus(taskId) {
    $.ajax({
        url: `${APP_URL}/${APP_NAME}/similarity-status/${taskId}/`,
        type: "GET",
        headers: { "X-CSRFToken": csrfToken },
        dataType: "json",
        success: function (data) {
            if (data.status === "running") {
                setTimeout(function () {
                    checkStatus(taskId);
                }, 1000); // Check every 1 second
            } else if (data.status === "success") {
                displayScores(JSON.parse(data.result));
            }
        },
        error: function (xhr, status, error) {
            console.error("Error checking similarity status:", xhr, status, error);
        }
    });
}

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

function displayScores(scores) {
    const table = document.getElementById("similarity");
    const queryImgs = Object.keys(scores);

    if (queryImgs.length > 0) {
        queryImgs.map(qImg => {
            const similarities = scores[qImg];
            qImg = qImg.replace("wit205_pdf216_", "wit1_man1_0")
            const row = table.insertRow();
            row.innerHTML = `<th>
                <img class="anno-img" src='${refToIIIF(qImg)}' alt="Annotation ${qImg}"><br>
                <h3><a href="${refToMirador(qImg)}" target="_blank">${qImg}</a></h3>
            </th>`;

            if (similarities && similarities.length){
                similarities.map(similarity => {
                    let [score, sImg] = similarity;
                    sImg = sImg.replace("wit205_pdf216_", "wit1_man1_0")
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
