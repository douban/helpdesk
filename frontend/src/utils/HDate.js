export function UTCtoLcocalTime (UTCTime) {
  // Params: UTCTime str
  let dateObj = new Date(UTCTime + '+00:00')
  return dateObj.toLocaleString()
}
