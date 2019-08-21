function predict() {
    var quotedFieldList = ['command'];
    var data = {};
    quotedFieldList.forEach(function (fieldName) {
        data[fieldName] = document.getElementById("input-" + fieldName).value;
    })

    var xhr = new XMLHttpRequest();
    xhr.open('POST', '/predict');
    xhr.setRequestHeader('Content-Type', 'application/json');
    xhr.onload = function () {
        if (xhr.status == 200) {
            // If you want a more impressive visualization than just
            // outputting the raw JSON, change this part of the code.
            var asJson = JSON.parse(xhr.responseText);
            var htmlResults = "<p>" + asJson['instance']['predicted_tokens'].join(' ') + "</p>";
            htmlResults += "<pre>" + JSON.stringify(asJson, null, 2) + "</pre>";

            document.getElementById("output").innerHTML = htmlResults;
        }
    };
    xhr.send(JSON.stringify(data));
}