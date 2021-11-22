export function cmp (a, b, attr) {
  let x = a
  let y = b
  if (attr !== undefined) {
    x = a[attr]
    y = b[attr]
  }
  if (!x && !y) {
    return 0
  } else if (!x) {
    return -1
  } else if (!y) {
    return 1
  }
  return (x > y) - (x < y)
}
