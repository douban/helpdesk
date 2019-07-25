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

export function getFirstValidElementFromArray (a, validator) {
  for (let i = 0; i < a.length; i++) {
    if (validator(a[i])) {
      return a[i]
    }
    if (a[i].children) {
      return getFirstValidElementFromArray(a[i].children, validator)
    }
  }
}

function hasTargetObject (element) {
  if (element.target_object !== undefined) {
    return true
  }
}

export function getFirstActionFromTree (tree) {
  return getFirstValidElementFromArray(tree, hasTargetObject)
}

export function addKeyForEachElement (tree, startingKey) {
  // startingKey is the head of key
  // if not undefined every key in tree will be startingKey-somename
  for (let i = 0; i < tree.length; i++) {
    tree[i].key = [startingKey, tree[i].name].filter(Boolean).join('-')
    if (tree[i].children) {
      tree[i].children = addKeyForEachElement(tree[i].children, tree[i].key)
    }
  }
  return tree
}
