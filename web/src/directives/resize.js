export default (() => {
  let resizeEvent
  return {
    inserted (el, binding) {
      let delta = 0
      if (binding.value) {
        delta = binding.value
      }
      el.style.overflow = 'auto'
      resizeEvent = () => {
        el.style.height = window.innerHeight - delta + 'px'
      }
      resizeEvent()
      window.addEventListener('resize', resizeEvent)
    },
    unbind () {
      window.removeEventListener('resize', resizeEvent)
    }
  }
})()
