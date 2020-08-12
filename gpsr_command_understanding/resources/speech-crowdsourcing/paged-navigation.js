var current = 1;
var moved = [];
var movedto = [];
let numPages = 0;
let pagesContainer = null;
let pageNumber = null;
let preNextValidator = null;
function setUpPages(container, nextValidator) {
    pagesContainer = container;
    preNextValidator = nextValidator;
    pageNumber = document.getElementById("page-number");
    let pages = container.querySelectorAll(".page");
    for (let i = 0; i < pages.length; i++) {
        pages[i].setAttribute("id", "p" + i.toString());
        pages[i].style.display = "none";
    }
    document.getElementById("p0").style.display = "block";
    current = 0;
    numPages = pages.length;
}
function effectivePage(pagenum) {
    let index = moved.indexOf(pagenum);
    if (index === -1) {
        return pagenum;
    }
    else {
        return movedto[index];
    }
}
function swap(vanish, appear) {
    pagesContainer.querySelector("#p" + vanish).style.display = "none";
    document.querySelector("#p" + appear).style.display = "";
}
function next() {
    var _a;
    let validationResult = (_a = preNextValidator(pagesContainer.querySelector("#p" + current))) !== null && _a !== void 0 ? _a : "";
    if (validationResult !== "") {
        alert(validationResult);
        return;
    }
    if (current === numPages - 1) {
        return;
    }
    current++;
    pageNumber.innerText = current.toString();
    swap(current - 1, current);
}
function back() {
    if (current === 0) {
        return;
    }
    current--;
    pageNumber.innerText = current.toString();
    swap(current + 1, current);
}
//# sourceMappingURL=paged-navigation.js.map