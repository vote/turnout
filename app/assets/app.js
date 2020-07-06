import "bootstrap";
import $ from "jquery";
import "popper.js";
import "./scss/app.scss";
import "./markdown"

$(document).ready(function() {
  $(".dropdown-expand-link").click(function(e) {
    e.preventDefault();
  });
});
