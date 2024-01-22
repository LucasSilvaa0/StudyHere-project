function flip_card(id) {
    card = document.getElementById(id)
    console.log(card.style.display)
    if (card.style.display == "") {
        card.style.display = "block"
    } else {
        card.style.display = "none"
    }
}

