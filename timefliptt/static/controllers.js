"use strict";

/* Constants */
const ESC_KEY = 27;
const ENTER_KEY = 13;

const ONE_HOUR = 60 * 60;
const ONE_DAY = 24 * ONE_HOUR;

const NAMES = [
    "teddy bears",
    "unicorns",
    "cats",
    "dogs",
    "bunnies",
    "drunk racoon",
    "friendly bears",
    "alcoholic beverages",
    "pints",
    "vast amount of alcohol",
    "garlic bread",
    "minimal amount of cheese",
    "tons of pizza",
    "moderate amount of salt",
    "problems",
    "issues",
    "solutions",
    "management",
    "pencils",
    "pens",
    "tons of paper clips",
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
    "Tasking on",
    "Declaring",
    "Allowing",
    "Integrating"
];

/* Utilities */
function randomName() {
    return ACTIONS.random() + " " + NAMES.random();
}

Array.prototype.random = function () {
  return this[Math.floor((Math.random()*this.length))];
};

class APICallError extends Error {
    constructor(metadata) {
        super(`Response code was ${metadata.status}`);
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
    let $newAction = $action.cloneNode(true);
    $newAction.innerHTML = button;
    $action.parentNode.replaceChild($newAction, $action);

    $newAction.addEventListener('click',(event) => {action(modal, event); });

    modal.show();
}

function showModalMessage($modal, message, scheme="alert-danger") {
     let $msg = $modal.querySelector('.modal-body');

     let $div = document.getElementById('tp-modalmessage').content.cloneNode(true);
     $div.querySelector('.placeholder').innerHTML = message;

     scheme.split(" ").forEach((cl) => {
        $div.querySelector('.alert').classList.add(cl);
    });

     $msg.insertBefore($div, $msg.firstChild);
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
            throw new APICallError(response);
        } else {
            return response.json();
        }
    });
}

function formatDuration(start, end) {
    let st = new Date(start);
    let en = new Date(end);

    let diff = Math.floor((en - st) / 1000); // in secs
    return formatDurationS(diff);
}

function formatDurationS(diff) {
    let diff_s = '';

    let mins = parseInt(diff / 60);
    let hours = parseInt(diff / 60 / 60);
    let days = parseInt(diff / 24 / 60 / 60);

    if (diff < 60 ) {
        diff_s = `${diff} sec${diff > 1 ? 's': ''}`;
    } else if (diff < 60 * 60) {
        let rem = diff - mins * 60;
        diff_s = `${mins} min${mins > 1? 's': ''} and ${rem} sec${rem > 1? 's': 's'}`;
    } else {
        let rem = parseInt((diff  - hours * 60 * 60) / 60);
        diff_s = `${hours} hour${hours > 1? 's': ''} and ${rem} min${rem > 1? 's': 's'}`;
    }

    return diff_s;
}

/* Controllers */
import { Controller } from "https://unpkg.com/@hotwired/stimulus@3.0.0/dist/stimulus.js";

let updateInterval = null;

export class TFConnectController extends Controller {
    static get targets() { return ["timeflips", "view", "inputTF", "connect", "name", "address", "battery", "facet", "link"]; }
    static get values() { return {id: Number}; }

    connect() {
        apiCall(`/timeflips/daemon`)
            .then((data) => {
                if (data.daemon_status === "connected") {
                    this.idValue = data.timeflip_device.id;
                    this.status();
                    this.viewTarget.hidden = false;
                    this.setInterval();
                } else {
                    this.listTF();
                }
            }).catch((error) => {
                showToast(error.message);
            });
    }

    setInterval() {
        clearInterval();
        updateInterval = window.setInterval(
            () => { this.status(); },
            15 * 1000
        );
    }

    clearInterval() {
        if (updateInterval != null) {
            window.clearInterval(updateInterval);
            updateInterval = null;
        }
    }

    listTF() {
        this.viewTarget.hidden = true;
        apiCall('/timeflips')
            .then((data) => {
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
            }).catch((error) => {
                showToast(error.message);
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
                this.setInterval();
            }).catch((error) => {
                showToast(error.message);
            });
    }

    status() {
        apiCall(`timeflips/${this.idValue}/handle`)
            .then((data) => {
                this.update_status(data);
            }).catch((error) => {
                this.listTF();
                this.clearInterval();
                showToast(error.message);
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
            this.clearInterval();
        });
    }
}

function deal_with_tf_info_error_422(metadata) {
    return metadata.json().then((data) => {
       let errors = [];
       ['address', 'name', 'password'].forEach((field) => {
           if (field in data.errors.json) {
               errors.push(`${field} (${data.errors.json[field][0]})`);
           }
       });
       return `Please correct field${ errors.length > 1 ? 's' : ''}: ${errors.join(', ')}`;
    });
}

export class TFAddController extends Controller {
    static get targets() { return ["list", "address", "password"]; }
    connect() {
        apiCall('devices/')
            .then((data) => {
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
            }).catch((error) => {
                showToast(error.message);
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
                    if ('metadata' in err && 'metadata' in err && err.metadata.status === 422) {
                        deal_with_tf_info_error_422(err.metadata).then((msg) => showToast(msg));
                    } else {
                        showToast(err.message);
                    }
                });
        }
    }
}

import { Chart, registerables } from 'https://cdn.jsdelivr.net/npm/chart.js@3.5.1/dist/chart.esm.js';

Chart.register(...registerables);

Date.prototype.resetTime =  function () {
    this.setSeconds(0);
    this.setMinutes(0);
    this.setHours(0);
};

export class GraphsController extends  Controller {
    static get targets() { return [
        "inputStartEnd", "inputStartDate", "inputEndDate", "inputPeriod",
        "inputCategories", "inputTasks",
        "cumulative", "perPeriod", "total"
    ]; }

    connect() {
        this.changePeriod();
        apiCall('categories/').then((data) => {
                data.categories.forEach((category)=> {
                    let $optcat = document.createElement("option");
                    $optcat.value = category.id;
                    $optcat.innerText = category.name;
                    this.inputCategoriesTarget.append($optcat);

                    category.tasks.forEach((task) => {
                        let $opttask = document.createElement("option");
                        $opttask.value = task.id;
                        $opttask.innerText = `${category.name} > ${task.name}`;
                        this.inputTasksTarget.append($opttask);
                    });
                });
            }).catch((err) => {
                showToast(err.message);
            });
    }

    changePeriod() {
        let start = new Date();
        let end = new Date();
        let v = this.inputStartEndTarget.value;
        this.inputPeriodTarget.value = ONE_DAY;

        if (v.startsWith('L')) { // last x days
            console.log(v.slice(1));
            end = new Date();
            end.resetTime();
            end.setDate(end.getDate() + 1);
            start = new Date(end);
            start.setDate(end.getDate() - Number(v.slice(1)));

            if (v === 'L1')
                this.inputPeriodTarget.value = ONE_HOUR;

        } else if (v === 'tw') {
            start = new Date();
            start.setDate(start.getDate() - (start.getDay() + 6) % 7); // previous monday
            start.resetTime();
            end = new Date(start.getFullYear(), start.getMonth(), start.getDate() + 7);
        } else if (v === 'tm') {
            start = new Date();
            start.setDate(1);
            start.resetTime();
            end = new Date(start);
            end.setMonth(start.getMonth() + 1);
            end.setDate(0);
            this.inputPeriodTarget.value = 24 * 60 * 60;
        } else if (v.startsWith('l')) { // last x weeks
            let n = Number(v[1]);
            end = new Date();
            end.setDate(start.getDate() - (start.getDay() + 6) % 7 + 7); // next monday
            end.resetTime();
            start = new Date(end);
            start.setDate(start.getDate() - n * 7);
        } else {
            showToast(`unknown value ${v}`);
        }

        this.inputStartDateTarget.valueAsDate = asUTC(start);
        this.inputEndDateTarget.valueAsDate = asUTC(end);

        this.refresh();
    }

    refresh() {
        let start = fromUTC(this.inputStartDateTarget.valueAsDate);
        let end = fromUTC(this.inputEndDateTarget.valueAsDate);

        let selected_cats = new Array(...this.inputCategoriesTarget.selectedOptions).map(opt => Number(opt.value));
        let selected_tasks = new Array(...this.inputTasksTarget.selectedOptions).map(opt => Number(opt.value));

        let query = `start_date=${asUTC(start).toISOString().slice(0, 10)}&end_date=${asUTC(end).toISOString().slice(0, 10)}`;

        if (selected_cats.length > 0)
            query += `&category=${selected_cats.join('&category=')}`;

        if (selected_tasks.length > 0)
            query += `&task=${selected_tasks.join('&task=')}`;

        let period = Number(this.inputPeriodTarget.value);
        this.makeCumulative(query);
        this.makePerPeriod(query, period, ONE_HOUR);
    }

    makeCumulative(query) {
        apiCall(`statistics/cumulative/tasks/?${query}`)
            .then((data) => {
                this.totalTarget.innerText = `Total: ${formatDurationS(data.cumulative_time)}`;
                this.cumulativeTarget.innerHTML = "";

                data.tasks.forEach((task) => {
                    let pc = (task.cumulative_time / data.cumulative_time * 100).toFixed(2);
                    let $div = document.createElement('div');
                    $div.classList.add('element');
                    $div.style.width = `${pc}%`;
                    $div.style.background = task.color;
                    $div.title = `${task.name} (${formatDurationS(task.cumulative_time)} - ${pc}%)`;
                    this.cumulativeTarget.append($div);
                });
            }).catch((err) => {
                showToast(err.message);
            });
    }

    makePerPeriod(query, period, subperiod) {
        let get_label = (date) => {
            let d = new Date(date);
            return `${(d.toLocaleTimeString())}`;
        };

        if (period >= 24 * 60 * 60 + 1) {
            get_label = (date) => {
                let d = new Date(date);
                let dp = new Date(date);
                dp.setSeconds(d.getSeconds() + period - 1);
                return `${d.toLocaleDateString()} ??? ${dp.toLocaleDateString()}`;
            };
        } else if (period >= 24 * 60 * 60) {
            get_label = (date) => {
                let d = new Date(date);
                return `${d.toLocaleDateString()}`;
            };
        } else if (period >= 60 * 60 + 1) {
            get_label = (date) => {
                let d = new Date(date);
                let dp = new Date(date);
                dp.setSeconds(d.getSeconds() + period - 1);
                return `${(d.toLocaleTimeString())} ??? ${dp.toLocaleTimeString()}`;
            };
        }

        apiCall(`statistics/periodic/${period}/tasks/?${query}`)
            .then((data) => {
                let labels = [];
                let datasets = {};
                let period_id = 0;

                data.periods.forEach((period) => {
                    labels.push(get_label(period.start));

                    period.tasks.forEach((task) => {
                        if(!(task.id in datasets)) {
                            datasets[task.id] = {
                                label: task.name,
                                backgroundColor: task.color,
                                data: Array(data.periods.length).fill(0)
                            };
                        }

                        datasets[task.id].data[period_id] = task.cumulative_time / subperiod;
                    });

                    period_id++;
                });

                let $canvas = document.createElement('canvas');
                this.perPeriodTarget.innerHTML = '';
                this.perPeriodTarget.append($canvas);

                new Chart($canvas, {
                    type: 'bar',
                    data: {
                        labels: labels,
                        datasets: Object.values(datasets)
                    },
                    options: {
                        aspectRatio: 2.5,
                        scales: {
                          x: {
                            stacked: true,
                          },
                          y: {
                            stacked: true,
                              title: {
                                display: true,
                                text: 'Number of hours'
                              },
                              ticks: {
                                stepSize: 2
                              }
                          }
                        }
                    }
                });
            }).catch((err) => {
                if ('metadata' in err && err.metadata.status == 403) {
                    showToast('Not allowed, since this would results in too many data!');
                } else {
                    showToast(err.message);
                }
            });
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
            }).catch((error) => {
                    showToast(error.message);
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
            }).catch((error) => {
                showToast(error.message);
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
                ).catch((error) => {
                    showToast(error.message);
                });
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
            }).catch((error) => {
                showToast(error.message);
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
        }).then((data) => {
                this.stopEdit();
                this.nameTarget.innerText = data.name;
                this.colorValue = data.color;
                this.colorTarget.style.backgroundColor = data.color;
            }).catch((error) => {
                showToast(error.message);
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
                ).catch((error) => {
                    showToast(error.message);
                });
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

export class TimeflipInfoController extends Controller {
    static get values() { return {id: Number}; }
    static get targets() { return ["inputFacet", "inputTask", "append", "tbody", "inputName", "inputPassword"]; }

    connect() {
        apiCall(`timeflips/${this.idValue}/facets/`)
            .then((data) => {
                data.facet_to_task.forEach((ftt) => this.addFTT(ftt));
            }).catch((error) => {
                showToast(error.message);
            });
    }

    createFTT() {
        apiCall(`categories/`)
            .then((data) => {
                // list tasks
                this.inputTaskTarget.innerHTML = ""; // remove previous

                data.categories.forEach((category) => {
                    category.tasks.forEach((task) => {
                        let $opt = document.createElement("option");
                        $opt.value = task.id;
                        $opt.innerText = `${category.name} > ${task.name}`;
                        this.inputTaskTarget.append($opt);
                    });
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
            }).catch((error) => {
                showToast(error.message);
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
        $ftt.querySelector('.task-color').style.background = ftt.task.color;
        $ftt.querySelector('.t-task').innerHTML = ftt.task.name;

        this.tbodyTarget.append($ftt);
    }

    cancel() {
        this.appendTarget.hidden = true;
    }

    submitFTT() {
        apiCall(
            `timeflips/${this.idValue}/facets/${this.inputFacetTarget.value}/`,
            'put',
            { task: this.inputTaskTarget.value }
            ).then((ftt) => {
                this.addFTT(ftt);
                this.appendTarget.hidden = true;
            }).catch((error) => {
                showToast(error.message);
            });
    }

    editInfo() {
        apiCall(`timeflips/${this.idValue}/handle`)
            .then((data) => {
                let $modal = document.querySelector('#timeflipInfoModal');
                let modal = new bootstrap.Modal($modal);
                this.inputNameTarget.value = data.name;
                this.inputPasswordTarget.value = data.password;

                $modal.querySelector('.action').addEventListener('click', () => {
                    apiCall(
                        `timeflips/${this.idValue}/handle`,
                        'put',
                        {name: this.inputNameTarget.value, password: this.inputPasswordTarget.value}
                        ).then((data) => {
                            modal.hide();
                            showToast('Info were updated', 'bg-info');
                        }).catch((error) => {
                            if ('metadata' in error && error.metadata.status === 401)  {
                                showToast('Please connect to TimeFlip first');
                            } else if ('metadata' in error && error.metadata.status === 422) {
                                deal_with_tf_info_error_422(error.metadata).then((msg) => showModalMessage($modal, msg));
                            } else {
                                showToast(error.message);
                            }
                        });
                });

                modal.show();
            }).catch((error) => {
                if ('metadata' in error && error.metadata.status === 401)  {
                    showToast('Please connect to TimeFlip first');
                } else {
                    showToast(error.message);
                }
            });
    }

    resetCalibration() {
        apiCall(`timeflips/${this.idValue}/handle`)
            .then((data) => {
                showModal(
                'Change Calibration',
                `Current calibration is <code>${data.calibration}</code> in database (device's calibration is <code>${data.device_calibration}</code>). Do you really want to change?`,
                "Change",
                (modal, event) => {
                    apiCall(
                        `timeflips/${this.idValue}/handle`, 'put', {change_calibration: true}
                        ).then((data) => {
                            modal.hide();
                            showToast(`Calibration was changed to <code class="text-white">${data.calibration}</code>.`, "bg-info");
                        }).catch((error) => {
                            showModalMessage(modal._element, error.message);
                        });
                });
            }).catch((error) => {
                if ('metadata' in error && error.metadata.status === 401)  {
                    showToast('Please connect to TimeFlip first');
                } else {
                    showToast(error.message);
                }
            });
    }

    fetchHistory() {
        showModal(
        'Fetch history',
        `Do you want to fetch history? This may take a few seconds!`,
        "Fetch",
        (modal, event) => {
            apiCall(
                `timeflips/${this.idValue}/history`, 'post'
                ).then((data) => {
                    showToast(`Fetched ${data.history_elements.length} history elements!`, "bg-info");
                    modal.hide();
                }).catch((error) => {
                    if ('metadata' in error && error.metadata.status === 401)  {
                        showModalMessage(modal._element, 'Please connect to TimeFlip first');
                    } else if ('metadata' in error && error.metadata.status === 409)  {
                        error.metadata.json().then(data => showModalMessage(modal._element, data.message));
                    } else {
                        showModalMessage(modal._element, error.message);
                    }
                });
        });
    }
}

export class FacetToTaskController extends Controller {
    static get values() { return {facet: Number, task: Number, device: Number}; }
    static get targets() { return [
        "taskName", "taskColor", "inputTask", "modifyTask", "viewTask",
        "viewBtn", "modifyBtn"
    ];
    }

    destroy() {
        let $element = this.element;
        showModal(
            "Delete correspondence",
            `Do you really want to delete correspondence to "${this.taskNameTarget.innerText}"?`,
            "Delete correspondence",
            (modal, event) => {
                apiCall(`timeflips/${this.deviceValue}/facets/${this.facetValue}/`, 'delete').then(
                    () => {
                        $element.parentNode.removeChild($element);
                        modal.hide();
                    }
                ).catch((error) => {
                    showToast(error.message);
                });
            });
    }

    edit() {
        apiCall(`categories/`)
            .then((data) => {
                this.inputTaskTarget.innerHTML = ""; // remove previous

                data.categories.forEach((category) => {
                    category.tasks.forEach((task) => {
                        let $opt = document.createElement("option");
                        $opt.value = task.id;
                        $opt.innerText = `${category.name} > ${task.name}`;
                        this.inputTaskTarget.append($opt);
                    });
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
                this.taskNameTarget.innerText = ftt.task.name;
                this.taskValue = ftt.task.id;
                this.taskColorTarget.style.background = ftt.task.color;

                this.stopEdit();
            });
    }

    startEdit() {
        this.modifyTaskTarget.hidden = false;
        this.viewTaskTarget.hidden = true;
        this.modifyBtnTarget.hidden = false;
        this.viewBtnTarget.hidden = true;
    }

    stopEdit() {
        this.modifyTaskTarget.hidden = true;
        this.viewTaskTarget.hidden = false;
        this.modifyBtnTarget.hidden = true;
        this.viewBtnTarget.hidden = false;
    }
}

export class HistoryController extends Controller {
    static get targets() { return [
        "tbody",
        "previous", "next", "size", "page",
        "inputCategories", "inputTasks",
        "inputBulkTask", "inputBulkComment"
    ]; }

    connect() {
        this.refresh();
        apiCall('categories/').then((data) => {
                data.categories.forEach((category)=> {
                    let $optcat = document.createElement("option");
                    $optcat.value = category.id;
                    $optcat.innerText = category.name;
                    this.inputCategoriesTarget.append($optcat);

                    category.tasks.forEach((task) => {
                        let $opttask = document.createElement("option");
                        $opttask.value = task.id;
                        $opttask.innerText = `${category.name} > ${task.name}`;
                        this.inputTasksTarget.append($opttask);
                    });
                });
            }).catch((err) => {
                showToast(err.message);
            });
    }

    showPage(page, page_size, extra_query='') {
        let query = `history/?page=${page}&page_size=${page_size}`;
        if (extra_query)
            query += extra_query;

        apiCall(query)
            .then((data) => {
                // paginate
                if (page > 0)
                    this.previousTarget.classList.remove('disabled');
                else
                    this.previousTarget.classList.add('disabled');
                if (page < data.total_pages - 1)
                    this.nextTarget.classList.remove('disabled');
                else
                    this.nextTarget.classList.add('disabled');

                this.pageTarget.innerHTML = "";
                for(let i=0; i < data.total_pages; i++) {
                    let $opt = document.createElement("option");
                    $opt.value = i;
                    $opt.innerText = i + 1;
                    this.pageTarget.append($opt);
                }
                this.pageTarget.value = page;

                // fill elements
                this.tbodyTarget.innerHTML = '';
                data.history.forEach((element) => {
                    this.addHistoryElement(element);
                });

            }).catch((error) => {
                if ('metadata' in error && error.metadata.status === 404)  {
                    showToast('The requested page does not exists');
                } else {
                    showToast(error.message);
                }
            });
    }

    addHistoryElement(element) {
        let $history = document.getElementById('tp-history').content.cloneNode(true);
        let $control = $history.querySelector('tr');

        $control.dataset.historyelmIdValue = element.id;
        $control.dataset.historyelmTaskValue = element.task !== null ? element.task.id : -1;
        $control.dataset.historyelmStartValue = element.start;
        $control.dataset.historyelmEndValue = element.end;

        $history.querySelector('.t-checkbox').checked = false;

        let $start = $history.querySelector('.t-start');
        let st = new Date(element.start);
        $start.innerText = `${st.toLocaleString()}`;

        let $dur = $history.querySelector('.t-dur');
        $dur.innerText = formatDuration(element.start, element.end);
        $dur.title = `${element.start} ??? ${element.end}`;
        new bootstrap.Tooltip($dur);

        $history.querySelector('.t-facet').innerText = element.original_facet;

        if(element.task !== null) {
            $history.querySelector('.t-task').innerText = element.task.name;
            $history.querySelector('.task-color').style.background = element.task.color;
        } else {
            $history.querySelector('.task-color').hidden = true;
        }

        if(element.comment !== null)
            $history.querySelector('.t-comment').innerText = element.comment;

        this.tbodyTarget.append($history);
    }

    paginate({params: {shift}}) {
        if (this.pageValue + shift < 0) {
            showToast('Fetch negative page?!?');
        } else {
            this.showPage(Number(this.pageTarget.value) + shift, this.sizeTarget.value);
        }
    }

    repaginate() {
        this.pageTarget.value = 0;
        this.refresh();
    }

    refresh() {
        let selected_cats = new Array(...this.inputCategoriesTarget.selectedOptions).map(opt => Number(opt.value));
        let selected_tasks = new Array(...this.inputTasksTarget.selectedOptions).map(opt => Number(opt.value));

        let extra_query = '';
        if (selected_cats.length > 0)
            extra_query += '&category=' + selected_cats.join('&category=');

        if (selected_tasks.length > 0)
            extra_query += '&task=' + selected_tasks.join('&task=');

        this.showPage(Number(this.pageTarget.value), Number(this.sizeTarget.value), extra_query);
    }

    toogleAll(event) {
        document.querySelectorAll('.t-checkbox').forEach((checkbox) => {
            checkbox.checked = event.target.checked;
        });
    }

    get checked() {
        let checked = [];
        document.querySelectorAll('.t-checkbox').forEach((checkbox) => {
            if (checkbox.checked === true)
                checked.push(Number(checkbox.parentElement.parentElement.dataset.historyelmIdValue));
        });

        return checked;
    }

    modifyTaskChecked() {
        let checked = this.checked;

        if (checked.length == 0) {
            showToast('Select elements for bulk modify');
        } else {
            apiCall(`categories/`)
            .then((data) => {
                this.inputBulkTaskTarget.innerHTML = ""; // remove previous
                let $opt = document.createElement("option");
                $opt.value = '-1';
                $opt.innerText = '** No task';
                this.inputBulkTaskTarget.append($opt);

                data.categories.forEach((category) => {
                    category.tasks.forEach((task) => {
                        $opt = document.createElement("option");
                        $opt.value = task.id;
                        $opt.innerText = `${category.name} > ${task.name}`;
                        this.inputBulkTaskTarget.append($opt);
                    });
                });

                let $modal = document.getElementById('bulkEditTaskModal');
                let modal = new bootstrap.Modal($modal);

                let $action = $modal.querySelector('.action');
                let $cloned = $action.cloneNode(true);

                $cloned.addEventListener('click', () => {
                   apiCall(`history/?id=${checked.join('&id=')}`, 'patch', {task: this.inputBulkTaskTarget.value})
                       .then((data) => {
                           this.refresh();
                           modal.hide();
                           showToast(`Updated ${checked.length} element${checked.length>1? 's': ''}`, 'bg-info');
                       }).catch((error) => {
                           showModalMessage($modal, error.message);
                       });
                });
                $action.parentNode.replaceChild($cloned, $action);

                modal.show();

            }).catch((error) => {
                showToast(error.message);
            });
        }
    }

    modifyCommentChecked() {
        let checked = this.checked;

        if (checked.length == 0) {
            showToast('Select elements for bulk modify');
        } else {
            this.inputBulkCommentTarget.value = ""; // remove previous

            let $modal = document.getElementById('bulkEditCommentModal');
            let modal = new bootstrap.Modal($modal);

            let $action = $modal.querySelector('.action');
            let $cloned = $action.cloneNode(true);

            $cloned.addEventListener('click', () => {
               apiCall(`history/?id=${checked.join('&id=')}`, 'patch', {comment: this.inputBulkCommentTarget.value})
                   .then((data) => {
                       this.refresh();
                       modal.hide();
                       showToast(`Updated ${checked.length} element${checked.length>1? 's': ''}`, 'bg-info');
                   }).catch((error) => {
                       showModalMessage($modal, error.message);
                   });
            });
            $action.parentNode.replaceChild($cloned, $action);

            modal.show();
        }
    }

    destroyChecked() {
        let checked = this.checked;

        if (checked.length == 0) {
            showToast('Select elements for bulk delete');
        } else {
            showModal(
                'Delete elements',
                `Do you really want to delete ${checked.length} element${checked.length>1? 's': ''}?`,
                'Delete',
                (modal, event) => {
                    apiCall(`history/?id=${checked.join('&id=')}`, 'delete')
                       .then((data) => {
                           this.refresh();
                           modal.hide();
                           showToast(`Delteted ${checked.length} element${checked.length>1? 's': ''}`, 'bg-info');
                       }).catch((error) => {
                           showModalMessage(modal._element, error.message);
                       });
                }
            );
        }
    }
}

function asUTC(date) {
    date.setMinutes(date.getMinutes() - date.getTimezoneOffset());
    return date;
}

function fromUTC(date) {
    date.setMinutes(date.getMinutes() + date.getTimezoneOffset());
    return date;
}

function fromHTMLDateTime(date, time) {
    let datetime = fromUTC(date.valueAsDate);
    time = fromUTC(time.valueAsDate);
    datetime.setHours(time.getHours());
    datetime.setMinutes(time.getMinutes());
    datetime.setSeconds(time.getSeconds());
    return asUTC(datetime).toISOString().slice(0, -1);
}

function toHTMLDateTime(datetime_str, date, time)  {
    datetime_str = asUTC(new Date(datetime_str));
    date.valueAsDate = datetime_str;
    time.valueAsDate = datetime_str;
}

export class HistoryElmController extends Controller {
    static get values() { return {id: Number, task: Number, start: String, end: String}; }
    static get targets() { return [
        "task", "inputTask", "modifyTask", "taskName", "taskColor",
        "start", "inputStartDate", "inputStartTime", "modifyStart",
        "duration", "inputEndDate", "inputEndTime", "modifyEnd",
        "comment", "inputComment", "modifyComment",
        "btn", "modifyBtn"
    ]; }

    destroy() {
        let $element = this.element;
        showModal(
            "Delete element",
            `Do you really want to delete this element?`,
            "Delete element",
            (modal, event) => {
                apiCall(`history/${this.idValue}/`, 'delete').then(
                    () => {
                        $element.parentNode.removeChild($element);
                        modal.hide();
                    }
                ).catch((error) => {
                    showToast(error.message);
                });
            });
    }

    edit() {
        apiCall(`categories/`)
            .then((data) => {
                // task
                this.inputTaskTarget.innerHTML = ""; // remove previous
                let $opt = document.createElement("option");
                $opt.value = '-1';
                $opt.innerText = '** No task';
                this.inputTaskTarget.append($opt);

                data.categories.forEach((category) => {
                    category.tasks.forEach((task) => {
                        $opt = document.createElement("option");
                        $opt.value = task.id;
                        $opt.innerText = `${category.name} > ${task.name}`;
                        this.inputTaskTarget.append($opt);
                    });
                });

                this.inputTaskTarget.value = this.taskValue;

                // start&end
                toHTMLDateTime(this.startValue, this.inputStartDateTarget, this.inputStartTimeTarget);
                toHTMLDateTime(this.endValue, this.inputEndDateTarget, this.inputEndTimeTarget);

                // comment
                this.inputCommentTarget.value = this.commentTarget.innerText;

                this.startEdit();

            }).catch((error) => {
                showToast(error.message);
            });
    }

    cancel() {
        this.stopEdit();
    }

    update() {
        apiCall(
            `history/${this.idValue}/`,
            'patch',
            {
                task: this.inputTaskTarget.value,
                start: fromHTMLDateTime(this.inputStartDateTarget, this.inputStartTimeTarget),
                end: fromHTMLDateTime(this.inputEndDateTarget, this.inputEndTimeTarget),
                comment: this.inputCommentTarget.value
            }).then((element) => {
                if (element.task !== null) {
                    this.taskNameTarget.innerText = element.task.name;
                    this.taskColorTarget.hidden = false;
                    this.taskColorTarget.style.background = element.task.color;
                    this.taskValue = element.task.id;
                } else {
                    this.taskValue = -1;
                    this.taskNameTarget.innerText = "";
                    this.taskColorTarget.hidden = true;
                }

                let st = new Date(element.start);
                this.startTarget.innerText = `${st.toLocaleString()}`;

                this.durationTarget.innerText = formatDuration(element.start, element.end);
                this.durationTarget.title = `${element.start} ??? ${element.end}`;

                if(element.comment !== null)
                    this.commentTarget.innerText = element.comment;

                this.stopEdit();
            }).catch((error) => {
                showToast(error.message);
            });
    }

    startEdit() {
        this.startTarget.hidden = true;
        this.modifyStartTarget.hidden = false;
        this.durationTarget.hidden = true;
        this.modifyEndTarget.hidden = false;

        this.taskTarget.hidden = true;
        this.modifyTaskTarget.hidden = false;

        this.commentTarget.hidden = true;
        this.modifyCommentTarget.hidden = false;

        this.btnTarget.hidden = true;
        this.modifyBtnTarget.hidden = false;
    }

    stopEdit() {
        this.startTarget.hidden = false;
        this.modifyStartTarget.hidden = true;
        this.durationTarget.hidden = false;
        this.modifyEndTarget.hidden = true;

        this.taskTarget.hidden = false;
        this.modifyTaskTarget.hidden = true;

        this.commentTarget.hidden = false;
        this.modifyCommentTarget.hidden = true;

        this.btnTarget.hidden = false;
        this.modifyBtnTarget.hidden = true;
    }
}