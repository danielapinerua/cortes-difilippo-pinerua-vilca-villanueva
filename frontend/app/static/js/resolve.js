// Mejora la pantalla "Atender solicitud": el motivo solo aparece si se elige Rechazar
// y el botón se habilita recién cuando hay una decisión. La validación REAL la hace
// el API; esto es solo comodidad (si JavaScript falla, el formulario igual funciona).
(function () {
  var form = document.getElementById("resolve-form");
  if (!form) return;
  var box = document.getElementById("reason-box");
  var btn = document.getElementById("resolve-btn");
  var reason = document.getElementById("rejection_reason");

  function update() {
    var chosen = form.querySelector('input[name="decision"]:checked');
    btn.disabled = !chosen;
    var reject = chosen && chosen.value === "reject";
    box.hidden = !reject;
    reason.required = !!reject;
    btn.className = "btn " + (reject ? "btn-danger" : "btn-primary");
  }
  form.addEventListener("change", update);
  update();
})();
