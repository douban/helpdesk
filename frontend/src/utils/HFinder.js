export function getElementFromArray (a, property, value, pathMark) {
  // :params a array to be search
  // :params property property name
  // :params value property value
  // :params property serve as path marker
  // :returns [foundObject, objectPath]
  // objectPath is a series of ``pathMark`` joined with '-', for example: test1-test2
  for (let i = 0; i < a.length; i++) {
    if (a[i][property] === value) {
      return [a[i], a[i][pathMark]]
    }
    if (a[i].children) {
      let childFound = getElementFromArray(a[i].children, property, value, pathMark)
      if (childFound) {
        return [
          childFound[0],
          [a[i][pathMark], childFound[1]].join('-')
        ]
      }
    }
  }
}
