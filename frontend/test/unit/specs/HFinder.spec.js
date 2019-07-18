import {getElementFromArray} from 'src/utils/HFinder'

describe('FinderTest', function () {
  it('testElementFromArray', function () {
    let exampleArray = [
      {
        key: '1',
        title: '功能导航加载中',
        name: 'test',
        url: '/#/'
      }]
    let findResult = getElementFromArray(exampleArray, 'name', 'test')
    expect(findResult.title.to.be.equal('功能导航加载中'))
  })
})
