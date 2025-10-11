const config = {
  theme: 'system',
  text: 'Get access',
}

const button = document.querySelector('body > button')
const update = () => {
  document.documentElement.dataset.theme = config.theme
  button.ariaLabel = config.text
  button.querySelector('& > span:last-of-type').innerText = config.text
}

const sync = (event) => {
  if (
    !document.startViewTransition ||
    event.target.controller.view.labelElement.innerText !== 'Theme'
  )
    return update()
  document.startViewTransition(() => update())
}
