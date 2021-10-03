"use strict";

import { Controller } from "https://unpkg.com/@hotwired/stimulus@3.0.0/dist/stimulus.js";

export default class extends Controller {
  static targets = ["name", "newname"];
  static values = { id: Number }

  edit() {
    let name = this.nameTarget.innerText;
    this.nameTarget.innerHTML = `<input type="test" value="${name}" data-action="change->category#change" data-category-target="newname" />`;
  }

  change() {
    fetch(`/api/categories/${this.idValue}/`, {
        method: 'put',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({'name': this.newnameTarget.value})
    })
    .then((response) => response.json())
    .then((data) => {
      this.nameTarget.innerText = data.name;
    });
  }
}