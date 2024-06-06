$(document).ready(function () {
    $('[data-toggle="tooltip"]').tooltip();
});

let cart = [];

document.addEventListener('DOMContentLoaded', (event) => {
    loadCart();
    updateCartCount();
    updateCartButtons();
});

function toggleCart(itemId) {
    const item = document.getElementById(`witness-${itemId}`);
    const itemDetails = {
        id: itemId,
        works: item.querySelector('.witness-works').innerText,
        idText: item.querySelector('.witness-id').innerText.replace('ID :', '').trim(),
        type: item.querySelector('.witness-type').innerText.replace('Type :', '').trim(),
        cote: item.querySelector('.witness-id_nb').innerText.replace('Cote :', '').trim(),
        place: item.querySelector('.witness-place').innerText.replace('Lieu de conservation :', '').trim(),
        dates: item.querySelector('.witness-dates').innerText.replace('Dates :', '').trim(),
        actors: item.querySelector('.witness-roles').innerText.replace('Acteurs historiques :', '').trim(),
    };

    const index = cart.findIndex(cartItem => cartItem.id === itemId);
    const button = document.getElementById(`cart-button-${itemId}`);
    const cartButton = document.querySelector('.button-container button');

    if (index === -1) {
        cart.push(itemDetails);
        button.innerHTML = '<i class="fa-solid fa-cart-arrow-down"></i> Retirer du Panier';
        button.classList.remove('btn-success');
        button.classList.add('btn-danger');
        cartButton.classList.add('animate-bounce');
        setTimeout(() => cartButton.classList.remove('animate-bounce'), 500);
    } else {
        cart.splice(index, 1);
        button.innerHTML = '<i class="fa-solid fa-cart-plus"></i> Ajouter au Panier';
        button.classList.remove('btn-danger');
        button.classList.add('btn-success');
        cartButton.classList.add('animate-shake');
        setTimeout(() => cartButton.classList.remove('animate-shake'), 500);
    }

    saveCart();
    updateCartCount();
}

function removeFromCart(itemId) {
    const index = cart.findIndex(cartItem => cartItem.id === itemId);
    if (index !== -1) {
        cart.splice(index, 1);
        saveCart();
        updateCartCount();
        updateCartButtons();
        viewCart();
    }

    const button = document.getElementById(`cart-button-${itemId}`);
    if (button) {
        button.innerHTML = '<i class="fa-solid fa-cart-plus"></i> Ajouter au Panier';
        button.classList.remove('btn-danger');
        button.classList.add('btn-success');
    }
}

function saveCart() {
    localStorage.setItem('cart', JSON.stringify(cart));
}

function loadCart() {
    const storedCart = localStorage.getItem('cart');
    if (storedCart) {
        cart = JSON.parse(storedCart);
    }
}

function updateCartCount() {
    document.getElementById('cart-count').innerText = cart.length;
}

function updateCartButtons() {
    cart.forEach(cartItem => {
        const button = document.getElementById(`cart-button-${cartItem.id}`);
        if (button) {
            button.innerHTML = '<i class="fa-solid fa-cart-arrow-down"></i> Retirer du Panier';
            button.classList.remove('btn-success');
            button.classList.add('btn-danger');
        }
    });
}

function viewCart() {
    const cartItemsList = document.getElementById('cart-items');
    cartItemsList.innerHTML = '';

    if (cart.length === 0) {
        cartItemsList.innerHTML = '<li class="list-group-item">Your cart is empty.</li>';
    } else {
        cart.forEach(item => {
            const itemDetails = `
                <h3>${item.works}</h3>
                <p><strong>ID :</strong> ${item.idText}</p>
                <p><strong>Type :</strong> ${item.type}</p>
                <p><strong>Cote :</strong> ${item.cote}</p>
                <p><strong>Lieu de conservation :</strong> ${item.place}</p>
                <p><strong>Dates :</strong> ${item.dates}</p>
                <p><strong>Acteurs historiques :</strong> ${item.actors}</p>
                <button class="btn btn-danger" onclick="removeFromCart('${item.id}')">
                    <i class="fa-solid fa-cart-arrow-down"></i> Retirer du Panier
                </button>
                <button class="btn btn btn-info">
                    <i class="fa-solid fa-code-compare"></i> Similarité
                </button>
            `;
            cartItemsList.innerHTML += `<li class="list-group-item">${itemDetails}</li>`;
        });
    }

    $('#cartModal').modal('show');
}

function checkout() {
    alert('Checkout not implemented yet.');
}
