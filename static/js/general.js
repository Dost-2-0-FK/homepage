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
