export function getElementFromArray (a, property, value) {
  for (let i = 0; i < a.length; i++) {
    if (a[property] === value) {
      return a[i]
    }
    if (a.children) {
      return getElementFromArray(a.children, property, value)
    }
  }
}
