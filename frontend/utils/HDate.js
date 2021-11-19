export function UTCtoLcocalTime (UTCTime) {
  // Params: UTCTime str
  const dateObj = new Date(UTCTime + '+00:00')
  return dateObj.toLocaleString()
}
