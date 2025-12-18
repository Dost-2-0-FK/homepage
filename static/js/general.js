addEventListener("scroll", (_) => {
  document.getElementById("main").classList.add("main_cleared");
});

document.addEventListener("DOMContentLoaded", (_) => {
  var scrollPosition = sessionStorage.getItem("scrollPosition");
  if (scrollPosition !== null && location.pathname.indexOf("/entry") == 0) {
    window.scrollTo({top: parseInt(scrollPosition, 10), behavior: "smooth"});
  }
});

window.addEventListener("beforeunload", () => {
  const override = sessionStorage.getItem("nextScrollTop");
  const pos = override !== null ? parseInt(override, 10) : Math.round(window.scrollY); 
  sessionStorage.setItem("scrollPosition", String(pos));
  sessionStorage.removeItem("nextScrollTop");
});

window.addEventListener("submit", (event) => {
  const form = event.target; 
  const btn = form.querySelector("button[type='submit']");
  if (btn && window.scrollY === 0) {
    sessionStorage.setItem("nextScrollTop", 25);
  }
});

function ToggleMailSender(member) {
  console.log("opening send to: ", "send-mail-" + member);
  if (document.getElementById("send-mail-" + member).style.display === 'none')
    document.getElementById("send-mail-" + member).style.display='block';
  else
    document.getElementById("send-mail-" + member).style.display='none';
}

function EditEntry(key) {
  var searchParams = new URLSearchParams(window.location.search);
  searchParams.set("entry-key", key);
  window.location.search = searchParams.toString();
}

function SendInReview(key) {
  fetch("/secret/entry/review/" + key, { method: "post" }) 
    .then( (response) => {
      if (!response.ok) {
        alert("Key " + key + " not found!");
      } else {
        alert("<3<3<3");
      }
    });
}

function AddElementToInp(list, name) {
  let inp = document.getElementById(list);
  if (inp.value != "") {
    inp.value += "; ";
  }
  inp.value += name;
}

document.getElementById("gm_form").addEventListener("submit", (event) => SubmitLstForm(event, "gm"));
document.getElementById("cbi_form").addEventListener("submit", (event) => SubmitLstForm(event, "cbi"));

async function SubmitLstForm(e, lst_name) {
  e.preventDefault(); 
  const form = e.target;
  const formData = new FormData(form);

  const response = await fetch("/secret/add/" + lst_name, {
    method: "POST",
    body: formData
  });

  if (response.ok) {
    const modalEl = document.getElementById(lst_name + "Modal");
    const modal = bootstrap.Modal.getInstance(modalEl) 
                  || new bootstrap.Modal(modalEl);
    modal.hide();
    form.reset();
    const full_name = (lst_name == "gm") ? "genetic_augmentations" : "computer_brain_interfaces";
    AddElementToInp(full_name, formData.get("abbr"));
  } else {
    alert("Failed to create " + lst_name);
  }
}
