var container = document.getElementById("packsCnt")
var openedContainer = document.getElementById("openedPacksCnt")
let pages = document.getElementsByClassName("albumPage")

fetch('/register')
    .then(response => response.json())
    .then(data => {
        console.log(data)
    });

for (i = 0; i < pages.length; i++) {
    text = pages[i].getElementsByTagName("h5")[0].innerText
    pages[i].getElementsByTagName("h5")[0].innerText = text + (i + 1)
    console.log(text = text + i)
}

let albumIndex = 1
showPages(albumIndex);

function changePage(n) {
    showPages(albumIndex += n)
}

function showPages(n) {
    if (n > pages.length) {
        albumIndex = 1
    }

    if (n < 1) {
        albumIndex = pages.length
    }

    for (i = 0; i < pages.length; i++) {
        pages[i].style.display = "none";
    }

    pages[albumIndex - 1].style.display = "block";
}

function test() {
    return console.log(date)
}

function countdown() {
    console.log(date.getFullYear(), date.getMonth(), date.getDate(), date.getHours(), date.getMinutes(), date.getSeconds())
    simplyCountdown('#countdown', {
        year: date.getFullYear(),
        month: date.getMonth() + 1,
        day: date.getDate(),
        hours: date.getHours(),
        minutes: date.getMinutes(),
        seconds: date.getSeconds() + 5,
        words: { //words displayed into the countdown
            days: { singular: '', plural: '' },
            hours: { singular: ':', plural: '' },
            minutes: { singular: ':', plural: '' },
            seconds: { singular: '', plural: '' }
        },
        plural: false,
        zeroPad: true,
        onEnd: function () { return claimPack(); }, //Callback on countdown end, put your own function here
    });
}

function claimPack() {
    let countdown = document.getElementById('countdown')
    let button = document.getElementById('claimButton')
    countdown.remove()
    button.innerText = 'Claim pack'
    button.setAttribute('type', 'submit')
    button.setAttribute('form', 'claim')
    button.setAttribute('class', 'btn btn-success')
}

function flip(e) {
    console.log(e)
    document.querySelector(`#${e.id}`).classList.add("hover")
    document.querySelector(`#${e.id}`).style.cursor = 'default'
    setTimeout(() => {
        document.querySelector(`#${e.id}`).classList.add("growDone")
    }, 600)
    return
}

function flipAll() {
    allCards = document.querySelectorAll(".flip-container")
    for (let i = 0; i < allCards.length; i++) {
        console.log(allCards[i])
        flip(allCards[i])
    }
    document.querySelector("#flipAllButton").style.display = 'None'
    document.querySelector("#placeButton").style.display = 'block'
}
