export function UTCtoLcocalTime (UTCTime) {
  // Params: UTCTime str
  console.log(UTCTime)
  let dateObj = new Date(UTCTime + '+00:00')
  console.log(dateObj)
  return dateObj.toLocaleString()
}
