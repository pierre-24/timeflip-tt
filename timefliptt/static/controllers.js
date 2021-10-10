"use strict";

/* Constants */
const ESC_KEY = 27;
const ENTER_KEY = 13;

const NAMES = [
    "teddy bears",
    "unicorns",
    "cats",
    "dogs",
    "bunnies",
    "alcoholic beverages",
    "pints",
    "garlic bread",
    "minimal amount of cheese",
    "tons of pizza",
    "moderate amount of salt",
    "problems",
    "issues",
    "solutions",
    "management",
    "pencils",
    "cars",
    "person in charge",
    "cuddles"
];

const ACTIONS = [
    "Repositioning",
    "Dealing with",
    "Acting on",
    "Empowering",
    "Removing",
    "Adding",
    "Creating",
    "Choosing",
    "Firing",
    "Tasking with",
];

/* Utilities */
function randomName() {
    return ACTIONS.random() + " " + NAMES.random();
}

Array.prototype.random = function () {
  return this[Math.floor((Math.random()*this.length))];
};

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

function showModal(title, message, button, action) {
    let $modal = document.getElementById('generalModal');

    $modal.querySelector('.modal-title').innerHTML = title;
    $modal.querySelector('.modal-body').innerHTML = message;

    let modal = new bootstrap.Modal($modal);
    let $action = $modal.querySelector('.action');

    $action.innerHTML = button;
    $action.addEventListener(
        'click',
        (event) => {action(modal, event); },
        {once: true});

    modal.show();
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

/* Controllers */
import { Controller } from "https://unpkg.com/@hotwired/stimulus@3.0.0/dist/stimulus.js";

export class TFConnectController extends Controller {
    static get targets() { return ["timeflips", "view", "inputTF", "connect", "name", "address", "battery", "facet"]; }
    static get values() { return {id: Number}; }

    connect() {
        apiCall(`/timeflips/daemon`).then((data) => {
            if (data.daemon_status === "connected") {
                this.idValue = data.timeflip_device.id;
                this.status();
            } else {
                this.list_timeflips();
            }
        });
    }

    list_timeflips() {
        apiCall('/timeflips').then((data) => {
            if ("timeflip_devices" in data && data.timeflip_devices.length > 0) {
                this.inputTFTarget.innerHTML = ''; // remove previous options, if any
                data.timeflip_devices.forEach((device) => {
                    let n = document.createElement('option');
                    n.value = device.id;
                    n.innerText = `${device.name} (${device.address})`;
                   this.inputTFTarget.append(n);
                });
            } else {
                let n = document.createElement('option');
                n.innerText = "No timeflip registered";
                this.inputTFTarget.append(n);
                this.connectTarget.hidden = true;
            }
            this.timeflipsTarget.hidden = false;
            this.connectTarget.disabled = false;
        });
    }

    connectTF() {
        if(this.inputTFTarget.value === "")
            return;

        this.connectTarget.disabled = true;
        apiCall(`timeflips/${this.inputTFTarget.value}/handle`, 'post')
            .then((data) => {
                this.idValue = this.inputTFTarget.value;
                this.update_status(data);
                this.timeflipsTarget.hidden = true;
                this.viewTarget.hidden = false;
            });
    }

    status() {
        apiCall(`timeflips/${this.idValue}/handle`)
            .then((data) => {
                this.update_status(data);
                this.viewTarget.hidden = false;
            });
    }

    update_status(data) {
        this.nameTarget.innerText = data.name;
        this.addressTarget.innerText = data.address;
        this.batteryTarget.innerText = data.battery;
        this.facetTarget.innerText = data.facet;
    }

    disconnectTF() {
        this.viewTarget.hidden = true;
        apiCall('timeflips/daemon', 'delete').then(() => {
            this.list_timeflips();
        });
    }
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
        $cat.querySelector('.card').dataset.categoryIdValue = category.id;
        $cat.querySelector('.category-name').innerText = category.name;

        // append tasks
        let $ul = $cat.querySelector('ul.list-group');
        if('tasks' in category) {
            category.tasks.forEach((task) => {
                let $task = document.querySelector('#tp-task').content.cloneNode(true);

                $task.querySelector('li').dataset.taskIdValue = task.id;
                $task.querySelector('li').dataset.taskColorValue = task.color;

                $task.querySelector('.task-name').innerText = task.name;
                $task.querySelector('.task-color').style.backgroundColor = task.color;

                $ul.append($task);
            });
        }

        // append node
        this.elmsTarget.append($cat);
    }

    newCategory() {
        this.nValue++;
        apiCall('categories/', 'post', {'name': randomName()})
            .then((data) => this.addCategory(data));
    }
}

export class CategoryController extends Controller {
    static get targets() { return ["name", "input", "view", "modify"]; }
    static get values() { return {id: Number}; }

    edit() {
        this.startEdit();
        this.inputTarget.value = this.nameTarget.innerText;
        this.inputTarget.focus();
    }

    update() {
        apiCall(`categories/${this.idValue}/`, 'put', {'name': this.inputTarget.value})
        .then((data) => {
            this.stopEdit();
            this.nameTarget.innerText = data.name;
        });
    }

    keyup(event) {
        if (event.keyCode === ESC_KEY) {
            this.stopEdit();
        } else if (event.keyCode === ENTER_KEY) {
            this.update();
        }
    }

    destroy() {
        let $element = this.element.parentNode;
        showModal(
            "Delete category",
            `Do you really want to delete "${this.nameTarget.innerText}" and all its tasks?`,
            "Delete category",
            (modal, event) => {
                apiCall(`categories/${this.idValue}/`, 'delete').then(
                    () => {
                        $element.parentNode.removeChild($element);
                        modal.hide();
                    }
                );
            });
    }

    get randomColor() {
        const hx = ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9', 'a', 'b', 'c', 'd', 'e', 'f'];
        return '#' + hx.random() + hx.random() + hx.random() + hx.random() + hx.random() + hx.random();
    }

    newTask() {
        let $task = document.querySelector('#tp-task').content.cloneNode(true);
        let $ul = this.element.querySelector('ul');

        apiCall(
            `categories/${this.idValue}/`,
            'post',
            {'name': randomName(), 'color': this.randomColor}
            ).then((task) => {
                $task.querySelector('li').dataset.taskIdValue = task.id;
                $task.querySelector('li').dataset.taskColorValue = task.color;

                $task.querySelector('.task-name').innerText = task.name;
                $task.querySelector('.task-color').style.backgroundColor = task.color;

                $ul.append($task);
            });
    }

    startEdit() {
        this.modifyTarget.hidden = false;
        this.viewTarget.hidden = true;
    }

    stopEdit() {
        this.modifyTarget.hidden = true;
        this.viewTarget.hidden = false;
    }
}

export class TaskController extends Controller {
    static get targets() { return ["name", "color", "inputName", "inputColor", "view", "modify"]; }
    static get values() { return {id: Number, color: String}; }

    edit() {
        this.startEdit();
        this.inputNameTarget.value = this.nameTarget.innerText;
        this.inputColorTarget.value = this.colorValue;
        this.inputNameTarget.focus();
    }

    update() {
        apiCall(`tasks/${this.idValue}/`, 'patch', {
            'name': this.inputNameTarget.value,
            'color': this.inputColorTarget.value
        })
        .then((data) => {
            this.stopEdit();
            this.nameTarget.innerText = data.name;
            this.colorValue = data.color;
            this.colorTarget.style.backgroundColor = data.color;
        });
    }

    keyup(event) {
        if (event.keyCode === ESC_KEY) {
            this.stopEdit();
        } else if (event.keyCode === ENTER_KEY) {
            this.update();
        }
    }

    destroy() {
        let $element = this.element;
        showModal(
            "Delete task",
            `Do you really want to delete "${this.nameTarget.innerText}"?`,
            "Delete task",
            (modal, event) => {
                apiCall(`tasks/${this.idValue}/`, 'delete').then(
                    () => {
                        $element.parentNode.removeChild($element);
                        modal.hide();
                    }
                );
            });
    }

    startEdit() {
        this.modifyTarget.hidden = false;
        this.viewTarget.hidden = true;
    }

    stopEdit() {
        this.modifyTarget.hidden = true;
        this.viewTarget.hidden = false;
    }
}