var current = 1; //the current page
var moved: number[] = []; //pages which have been moved by the randomization
var movedto: number[] = [];
let numPages = 0;
let pagesContainer: HTMLElement = null;
let pageNumber: HTMLElement = null;

let preNextValidator: (arg0: HTMLElement) => boolean = null

function setUpPages(container: HTMLElement, nextValidator: (arg0: HTMLElement) => boolean){
    pagesContainer = container
    preNextValidator = nextValidator
    pageNumber = document.getElementById("page-number")
    let pages: any = container.querySelectorAll(".page")

    // Give pages index IDs
    for (let i = 0; i < pages.length; i++) {
        // IDs can't start with a number. Some things break if they do
        pages[i].setAttribute("id", "p"+i.toString())
        pages[i].style.display = "none"
    }

    document.getElementById("p0").style.display = "block";
    current = 0;
    numPages = pages.length
}

//takes randomization into account
function effectivePage(pagenum: number) {
    let index = moved.indexOf(pagenum);
    if (index === -1) {
        return pagenum;
    } else {
        return movedto[index];
    }
}

//make one vanish and the other appear
function swap(vanish: number, appear: number) {
    (<HTMLElement>pagesContainer.querySelector("#p"+vanish)).style.display = "none";
    (<HTMLElement>document.querySelector("#p"+appear)).style.display = "";
}

//go to the next page
function next() {
    let validationResult = preNextValidator(pagesContainer.querySelector("#p" + current)) ?? ""
    if (validationResult !== "") {
        alert(validationResult)
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