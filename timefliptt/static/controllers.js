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

function showToast(message, scheme="bg-danger") {
    let $toast = document.getElementById('tp-toast').content.cloneNode(true);

    $toast.querySelector('.toast-body').innerHTML = message;
    let $t = $toast.querySelector('.toast');
    scheme.split(" ").forEach((cl) => {
        $t.classList.add(cl);
    });
    document.getElementById('toasts').append($toast);

    new bootstrap.Toast($t).show();
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
            showToast(`Error code was ${response.status} while calling <code class="text-white">${address}</code>`);
            throw new APICallError(response.status, response);
        } else {
            return response.json();
        }
    });
}

/* Controllers */
import { Controller } from "https://unpkg.com/@hotwired/stimulus@3.0.0/dist/stimulus.js";

export class TFConnectController extends Controller {
    static get targets() { return ["timeflips", "view", "inputTF", "connect", "name", "address", "battery", "facet", "link"]; }
    static get values() { return {id: Number}; }

    connect() {
        apiCall(`/timeflips/daemon`).then((data) => {
            if (data.daemon_status === "connected") {
                this.idValue = data.timeflip_device.id;
                this.status();
            } else {
                this.listTF();
            }
        });
    }

    listTF() {
        apiCall('/timeflips').then((data) => {
            if ("timeflip_devices" in data && data.timeflip_devices.length > 0) {
                this.inputTFTarget.innerHTML = ''; // remove previous options, if any
                this.connectTarget.hidden = false;
                data.timeflip_devices.forEach((device) => {
                    let n = document.createElement('option');
                    n.value = device.id;

                    if(device.name != null)
                        n.innerText = `${device.name} (${device.address})`;
                    else
                        n.innerText = device.address;

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
        this.linkTarget.href = `/timeflip-${this.idValue}`;
    }

    disconnectTF() {
        this.viewTarget.hidden = true;
        apiCall('timeflips/daemon', 'delete').then(() => {
            this.listTF();
        });
    }
}

export class TFAddController extends Controller {
    static get targets() { return ["list", "address", "password"]; }
    connect() {
        apiCall('devices/').then((data) => {
            this.listTarget.innerHTML = '';

            data.discovered.forEach((device) => {
                if (device.id < 0) {

                let $b = document.createElement("button");
                $b.classList.add("btn");
                $b.classList.add("btn-primary");
                $b.innerText = `${device.name} (${device.address})`;
                $b.addEventListener('click', () => {
                    this.addressTarget.value = device.address;
                });
                this.listTarget.append($b);
                }
            });

            if (this.listTarget.childElementCount === 0) {
                this.listTarget.innerText = "No (new) devices found :'(";
            }
        });
    }

    addTF() {
        if (this.addressTarget.value === "" || this.passwordTarget.value === "") {
            showToast("Missing data");
        } else {
            apiCall(
                'timeflips/',
                "post",
                {
                    address: this.addressTarget.value,
                    password: this.passwordTarget.value
                }).then((data) => {
                    // update the list!
                    const event = new CustomEvent('addTF');
                    window.dispatchEvent(event);

                    // and display toast
                    showToast("Device successfully added!", "bg-primary");
                }).catch((err) => { // be more explicit!
                    if (err.metadata.status === 422) {
                        err.metadata.json().then((data) => {
                           let msg = 'Please correct the following fields: ';
                           if ('address' in data.errors.json) {
                               msg += `address (${data.errors.json.address[0]})`;
                           }
                           if ('password' in data.errors.json) {
                               if ('address' in data.errors.json)
                                   msg += ', ';
                               msg += `password (${data.errors.json.password[0]})`;
                           }
                           showToast(msg);
                        });
                    }
                });
        }
    }
}

export class CategoriesController extends Controller {
    static get targets() { return ["elms"]; }

    connect() {
        let _this = this;
        apiCall('categories/')
        .then(function (data) {
            data.categories.forEach((category) => {
                _this.addCategory(category);
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

export class FacetsToTaskController extends Controller {
    static get values() { return {id: Number}; }
    static get targets() { return ["inputFacet", "inputTask", "append", "tbody"]; }

    connect() {
        apiCall(`timeflips/${this.idValue}/facets/`)
            .then((data) => {
                data.facet_to_task.forEach((ftt) => this.addFTT(ftt));
            });
    }

    newFTT() {
        apiCall(`tasks/`)
            .then((data) => {
                // list tasks
                this.inputTaskTarget.innerHTML = ""; // remove previous
                data.tasks.forEach((task) => {
                    let $opt = document.createElement("option");
                    $opt.value = task.id;
                    $opt.innerText = task.name;
                    this.inputTaskTarget.append($opt);
                });

                // list facets
                this.inputFacetTarget.innerHTML = "";
                for(let i=0; i < 64; i++) {
                    if (this.element.querySelectorAll( `.ftt-facet-${i}`).length === 0) {
                        let $opt = document.createElement("option");
                        $opt.value = i;
                        $opt.innerText = i;
                        this.inputFacetTarget.append($opt);
                    }
                }

                // send to bottom
                let $parent = this.appendTarget.parentNode;
                let $e = this.appendTarget.cloneNode(true);
                $parent.removeChild(this.appendTarget);
                $parent.append($e);

                this.appendTarget.hidden = false;
            });
    }

    submitNewFTT() {
        apiCall(
            `timeflips/${this.idValue}/facets/${this.inputFacetTarget.value}/`,
            'put',
            { task: this.inputTaskTarget.value }
            ).then((ftt) => {
                this.addFTT(ftt);
                this.appendTarget.hidden = true;
            });
    }

    addFTT(ftt) {
        let $ftt = document.querySelector('#tp-facettotask').content.cloneNode(true);

        let $main = $ftt.querySelector('tr');
        $main.dataset.facettotaskFacetValue = ftt.facet;
        $main.dataset.facettotaskDeviceValue = this.idValue;
        $main.dataset.facettotaskTaskValue = ftt.task.id;
        $main.classList.add(`ftt-facet-${ftt.facet}`);

        $ftt.querySelector('.t-facet').innerText = ftt.facet;
        $ftt.querySelector('.t-task').innerHTML = ftt.task.name;

        this.tbodyTarget.append($ftt);
    }
}

export class FacetToTaskController extends Controller {
    static get values() { return {facet: Number, task: Number, device: Number}; }
    static get targets() { return ["task", "inputTask", "modify"]; }

    destroy() {
        let $element = this.element;
        showModal(
            "Delete correspondence",
            `Do you really want to delete correspondence to "${this.taskTarget.innerText}"?`,
            "Delete correspondence",
            (modal, event) => {
                apiCall(`timeflips/${this.deviceValue}/facets/${this.facetValue}/`, 'delete').then(
                    () => {
                        $element.parentNode.removeChild($element);
                        modal.hide();
                    }
                );
            });
    }

    edit() {
        apiCall(`tasks/`)
            .then((data) => {
                this.inputTaskTarget.innerHTML = ""; // remove previous
                data.tasks.forEach((task) => {
                    let $opt = document.createElement("option");
                    $opt.value = task.id;
                    $opt.innerText = task.name;
                    this.inputTaskTarget.append($opt);
                });

                this.inputTaskTarget.value = this.taskValue;

                this.startEdit();
            });
    }

    cancel() {
        this.stopEdit();
    }

    update() {
        apiCall(
            `timeflips/${this.deviceValue}/facets/${this.facetValue}/`,
            'put',
            { task: this.inputTaskTarget.value }
            ).then((ftt) => {
                this.taskTarget.innerText = ftt.task.name;
                this.taskValue = ftt.task.id;

                this.stopEdit();
            });
    }

    startEdit() {
        this.modifyTarget.hidden = false;
        this.taskTarget.hidden = true;
    }

    stopEdit() {
        this.modifyTarget.hidden = true;
        this.taskTarget.hidden = false;
    }
}