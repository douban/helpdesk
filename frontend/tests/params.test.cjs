const assert = require('node:assert/strict')
const fs = require('node:fs')
const path = require('node:path')
const vm = require('node:vm')
const { test } = require('node:test')
const Ajv = require('ajv')

function loadComponent (name) {
  const source = fs.readFileSync(path.join(__dirname, '../components', name + '.vue'), 'utf8')
  const script = source.match(/<script>([\s\S]*?)<\/script>/)[1]
    .replace("import Ajv from 'ajv'", '')
    .replace('export default', 'module.exports =')
  const sandbox = { module: { exports: {} }, Ajv }
  vm.runInNewContext(script, sandbox, { filename: name + '.vue' })
  return sandbox.module.exports
}

const dynamicForm = loadComponent('DynamicForm')
const hform = loadComponent('HForm')

test('DynamicForm retains false and numeric zero and removes empty fields', () => {
  const context = {
    formData: {},
    $set: (data, key, value) => { data[key] = value },
    $delete: (data, key) => { delete data[key] },
    $emit: () => {}
  }
  for (const [key, value] of Object.entries({ flag: false, count: 0, name: 'test' })) {
    dynamicForm.methods.updateForm.call(context, key, value)
  }
  assert.deepEqual(context.formData, { flag: false, count: 0, name: 'test' })
  for (const value of ['', null, undefined]) {
    dynamicForm.methods.updateForm.call(context, 'name', value)
    assert.equal(Object.hasOwn(context.formData, 'name'), false)
  }
})

test('HForm submits false and integer zero and omits empty strings', async () => {
  let submitted
  const context = {
    canSubmit: true,
    form: { validateFields: callback => callback(null, {}) },
    formData: { flag: false, count: 0, typedZero: '0', blank: '', unset: undefined, cleared: null },
    actionName: 'test',
    actionDefinition: {
      provider_type: 'airflow',
      params: {
        flag: { type: 'boolean' }, count: { type: 'integer' }, typedZero: { type: 'integer' },
        blank: { type: 'string' }, unset: { type: 'string' }, cleared: { type: 'string' }
      },
      params_json_schema: {
        type: 'object', required: ['flag', 'count'],
        properties: { flag: { type: 'boolean' }, count: { type: 'integer' } }
      }
    },
    formAjv: new Ajv(),
    $axios: options => {
      submitted = JSON.parse(options.data)
      return Promise.resolve({})
    },
    handleSubmitResult: () => {},
    errorAsNotification: error => { throw new Error(error) }
  }
  hform.methods.handleSubmit.call(context, { preventDefault: () => {} })
  await new Promise(resolve => setImmediate(resolve))
  assert.deepEqual(submitted, { flag: false, count: 0, typedZero: 0 })
  assert.equal(context.canSubmit, true)
})

test('HForm initializes boolean and integer defaults without coercion', () => {
  let backfill
  let deferred
  const context = {
    form: { resetFields: () => {} },
    schema: [
      { name: 'flag', default: false }, { name: 'count', default: 0 },
      { name: 'empty', default: null }
    ],
    $nextTick: callback => { deferred = callback },
    handleInput: data => { backfill = JSON.parse(JSON.stringify(data)) }
  }
  hform.methods.resetForm.call(context)
  deferred()
  assert.deepEqual(backfill, { flag: false, count: 0 })
})
