"use strict";

const ESC_KEY = 27;

import { Controller } from "https://unpkg.com/@hotwired/stimulus@3.0.0/dist/stimulus.js";

class APICallError extends Error {
    constructor(status, metadata) {
        super(`Response code was ${status}`);
        this.metadata = metadata;
    }
}

function showToast(title, message) {
    let $toast = document.getElementById('tp-toast').content.cloneNode(true);
    $toast.querySelectorAll('.toast-title')[0].innerHTML = title;
    $toast.querySelectorAll('.toast-body')[0].innerHTML = message;
    document.getElementById('toasts').append($toast);

    new bootstrap.Toast(document.querySelector('.toast:last-child')).show();
}


function apiCall(address, method='get', body= null) {
    let params = {
        headers: {
          'Content-Type': 'application/json'
        },
        method: method,
    };

    if (body) {
        params.body = JSON.stringify(body);
    }

    return fetch(`/api/${address}`, params).then(function (response) {
        if (!response.ok) {
            showToast('Error', `Error code was ${response.status} while calling <code>${address}</code>`);
            throw new APICallError(response.status, response);
        } else {
            return response.json();
        }
    });
}

export class CategoriesController extends Controller {
    static get targets() { return ["elms"]; }
    static get values() { return {n: Number}; }

    connect() {
        let _this = this;
        apiCall('categories/')
        .then(function (data) {
            data.categories.forEach((category) => {
                _this.addCategory(category);
                _this.nValue++;
            });
        });
    }

    addCategory(category) {
        let $cat = document.querySelector('#tp-category').content.cloneNode(true);

        // set id and name
        $cat.querySelectorAll('.card-title')[0].dataset.categoryIdValue = category.id;
        $cat.querySelectorAll('.category-label')[0].innerText = category.name;

        // append node
        this.elmsTarget.append($cat);
    }

    newCategory() {
        this.nValue++;
        apiCall('categories/', 'post', {'name': `New category #${this.nValue}`})
            .then((data) => this.addCategory(data));
    }
}

export class CategoryController extends Controller {
    static get targets() { return ["label", "input"]; }
    static get values() { return {id: Number}; }

    edit() {
        this.labelTarget.hidden = true;
        this.inputTarget.hidden = false;
        this.inputTarget.value = this.labelTarget.innerText;
    }

    update() {
        apiCall(`categories/${this.idValue}/`, 'put', {'name': this.inputTarget.value})
        .then((data) => {
            this.cancel();
            this.labelTarget.innerText = data.name;
        });
    }

    cancel() {
        this.labelTarget.hidden = false;
        this.inputTarget.hidden = true;
    }

    keyup(event) {
        if (event.keyCode === ESC_KEY) {
            this.cancel();
        }
    }
}