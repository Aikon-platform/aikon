let scores = null;

function getAnnoRef(imgRef) {
    imgRef = imgRef.split("_");
    const digitRef = `${imgRef[0]}_${imgRef[1]}`;
    return annoRefs.filter(ref => ref.startsWith(digitRef))[0];
}
function refToIIIF(imgRef){
    imgRef = imgRef.split("_");
    const imgCoord = imgRef.pop().replace(".jpg", "");
    const imgName = imgRef.join("_");
    return `${CANTALOUPE_APP_URL}/iiif/2/${imgName}.jpg/${imgCoord}/full/0/default.jpg`;
}

function refToMirador(imgRef){
    /* TODO: Factorize using getAnnoRef function */
    imgRef = imgRef.split("_");
    const digitRef = `${imgRef[0]}_${imgRef[1]}`;
    const annoRef = annoRefs.filter(ref => ref.startsWith(digitRef))[0];
    const manifest = `${APP_URL}/${APP_NAME}/iiif/${MANIFEST_V2}/${annoRef}/manifest.json`;
    return `${SAS_APP_URL}/index.html?iiif-content=${manifest}&canvas=${parseInt(imgRef[2])}`;
}

function refToChange(imgRef){
    const witNumber = imgRef.match(/wit(\d+)_/)[1];
    return `/${APP_NAME}-admin/webapp/witness/${witNumber}/change/`;
}

function getImageInfo(imgRef) {
    const imgInfo = {};
    imgInfo.witNumber = imgRef.match(/wit(\d+)_/)[1];
    imgInfo.canvasNumber = parseInt(imgRef.match(/_(\d+)_/)[1], 10) ;
    imgInfo.coordinates = imgRef.match(/_(\d+,\d+,\d+,\d+)\.jpg$/)[1];
    imgInfo.annoRef = getAnnoRef(imgRef);
    return imgInfo;
}

function getWitnessTitle(number) {
    let prefix = `${WIT_CAP} #${number}${APP_LANG === "en" ? ": " : " : "}`;
    let options = document.getElementsByTagName('option');
    for (let i = 0; i < options.length; i++) {
        if (options[i].text.startsWith(prefix)) {
            return options[i].text.replace(prefix, '');
        }
    }
    return null;
}

function getCheckedRefs(checked_ref) {
    let checkedAnnoRefs = [];
    checkedAnnoRefs.push(checked_ref)
    const options = document.querySelectorAll('#multi-select option:checked');

    options.forEach(function(option) {
        checkedAnnoRefs.push(option.value);
    });

    return checkedAnnoRefs;
}

const displayScores = (scores) => {
    const table = document.getElementById("similarity");
    table.innerHTML = "";
    const queryImgs = viewOrder ? Object.keys(scores).sort() : Object.keys(scores);

    if (queryImgs.length > 0) {
        queryImgs.map(qImg => {
            const similarities = scores[qImg];
            const row = table.insertRow();
            row.innerHTML = `<th>
                <p>
                    <a href="${refToChange(qImg)}" target="_blank">
                        ${WIT_CAP} #${getImageInfo(qImg).witNumber}
                    </a>
                    (<a href="${refToMirador(qImg)}" target="_blank">${APP_LANG === "en" ? "view" : "vue"} ${getImageInfo(qImg).canvasNumber}</a>)
                </p>
                <a href="${refToIIIF(qImg)}" target="_blank">
                    <div class="img-wrap">
                        <img class="anno-img" src='${refToIIIF(qImg)}' alt="Annotation ${qImg}">
                        <div class="img-description-layer">
                            <p class="img-description">
                                <span>${getWitnessTitle(getImageInfo(qImg).witNumber)}</span>
                            </p>
                        </div>
                    </div>
                </a>
            </th>`;

            if (similarities && similarities.length){
                similarities.map(similarity => {
                    let [score, sImg] = similarity;
                    const sCell = row.insertCell();
                    sCell.innerHTML = `
                        <p>
                            <a href="${refToChange(sImg)}" target="_blank">
                                ${WIT_CAP} #${getImageInfo(sImg).witNumber}
                            </a>
                            (<a href="${refToMirador(sImg)}" target="_blank">${APP_LANG === "en" ? "view" : "vue"} ${getImageInfo(sImg).canvasNumber}</a>)
                        </p>
                        <a href="${refToIIIF(sImg)}" target="_blank">
                            <div class="img-wrap">
                                <img class="anno-img" src='${refToIIIF(sImg)}' alt="Annotation ${sImg}">
                                <div class="img-description-layer">
                                    <p class="img-description">
                                        <span>${getWitnessTitle(getImageInfo(sImg).witNumber)}</span>
                                    </p>
                                </div>
                            </div>
                        </a>
                        <div class="form-container">
                            <form class="category-form">
                                <input type="hidden" class="img_1" value="${qImg}">
                                <input type="hidden" class="img_2" value="${sImg}">
                                <input type="hidden" class="anno_ref_1" value="${getImageInfo(qImg).annoRef}">
                                <input type="hidden" class="anno_ref_2" value="${getImageInfo(sImg).annoRef}">
                                <label for="">1</label>
                                <input id="category1" type="checkbox" name="category" value="1">
                                <label for="" class="hspace">2</label>
                                <input id="category2" type="checkbox" name="category" value="2">
                                <label for="" class="hspace">3</label>
                                <input id="category3" type="checkbox" name="category" value="3">
                                <label for="" class="hspace">4</label>
                                <input id="category4" type="checkbox" name="category" value="4">
                                <label for="" class="hspace">5</label>
                                <input id="category5" type="checkbox" name="category" value="5">
                            </form>
                        </div>
                        `;
                    });
            }
        })
    } else {
        const emptyRow = table.insertRow();
        const cell = emptyRow.insertCell(0);
        cell.innerHTML = APP_LANG === "en" ? `Similarity scores were not computed for these ${WIT}es` :
            `Les scores de similarité n'ont pas été calculés pour ces ${WIT}s`;
    }

    document.querySelectorAll('.category-form').forEach((form) => {
        let img_1 = form.querySelector('.img_1').value;
        let img_2 = form.querySelector('.img_2').value;
        fetch(`/${APP_NAME}/retrieve-category/?img_1=${img_1}&img_2=${img_2}`, {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': CSRF_TOKEN
            },
        }).then(response => response.json())
        .then(data => {
            let category = data.category;
            let category_x = data.category_x;
            if (category) {
                form.querySelector(`#category${category}`).checked = true;
            }
            if (category_x.includes(Number(USER_ID))) {
                form.querySelector('#category5').checked = true;
            }
        });

        form.addEventListener('change', (event) => {
            if (event.target.name === 'category' && event.target.id !== 'category5') {
                form.querySelectorAll('input[name="category"]:not(#category5):checked').forEach((checkbox) => {
                    if (checkbox !== event.target) checkbox.checked = false;
                });
            }
            let img_1 = form.querySelector('.img_1').value;
            let img_2 = form.querySelector('.img_2').value;
            let anno_ref_1 = form.querySelector('.anno_ref_1').value;
            let anno_ref_2 = form.querySelector('.anno_ref_2').value;
            let category = form.querySelector('input[name="category"]:not(#category5):checked');
            let category_x = form.querySelector('#category5:checked');
            form.querySelectorAll('input[name="category"]').forEach((checkbox) => {
                checkbox.disabled = true;
            });
            let data = {
                'img_1': img_1,
                'img_2': img_2,
                'anno_ref_1': anno_ref_1,
                'anno_ref_2': anno_ref_2,
                'category': category ? category.value : null,
                'category_x': category_x ? category_x.value : null,
            };
            fetch(`/${APP_NAME}/save-category/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': CSRF_TOKEN
                },
                body: JSON.stringify(data)
            }).then(response => response.json())
            .then(data => {
				form.querySelectorAll('input[name="category"]').forEach((checkbox) => {
					checkbox.disabled = false;
				});
			});
        });
    });
}

function sendScoreRequest(annoRefs, maxRows, showCheckedRef) {
    return fetch(`${APP_URL}/${APP_NAME}/compute-score`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': CSRF_TOKEN
        },
        body: JSON.stringify({ annoRefs: annoRefs, maxRows: maxRows, showCheckedRef: showCheckedRef }),
    })
    .then(response => response.json()) // This line is needed to parse the response as JSON
    .then(score => {
        scores = score
        displayScores(score);
    })
    .catch(error => {
        console.error('Error sending data to the server:', error);
    });
}

$(document).on('change', "#viewOrder", function() {
    displayScores(scores);
});
