export default (value) => {
  if (!value) return ''
  value /= 1000
  let hours = Math.floor(value / 3600)
  value %= 3600
  let minutes = Math.floor(value / 60)
  let seconds = value % 60
  hours = hours < 10 ? '0' + hours : hours
  minutes = minutes < 10 ? '0' + minutes : minutes
  seconds = seconds < 10 ? '0' + seconds : seconds
  return `${hours}:${minutes}:${seconds}`
}
