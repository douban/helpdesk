<template>
  <a-layout :style="{ background: '#fff', padding: '24px', margin: '0 0 0 24px', minHeight: '280px' }">
    <a-divider orientation="left"><h3>{{name}}</h3></a-divider>
    <div
      v-show="resultVisible"
      :class="['ant-alert', 'ant-alert-' + resultType, 'ant-alert-no-icon']"
      style="margin: 16px;"
      v-html="submitResult"
    >
    </div>
    <a-alert
      :message="description"
      type="info"
      :style="{ margin: '16px' }"
    />
    <a-col>
      <a-form
      :form="form"
      @submit="handleSubmit">
        <dynamic-form
          :schema="schema"
          v-model="formData">
        </dynamic-form>
        <a-form-item
          :wrapper-col="{ span: 12, offset: 5 }"
        >
          <a-button type="primary" @click="handleSubmit">Submit</a-button>
        </a-form-item>
      </a-form>
    </a-col>
  </a-layout>

</template>

<script>
import DynamicForm from './DynamicForm'
import {HRequest} from '../utils/HRequests'
import AFormItem from 'ant-design-vue/es/form/FormItem'
export default {
  name: 'HForm',
  components: {
    AFormItem,
    DynamicForm
  },
  data () {
    return {
      formData: {},
      form: this.$form.createForm(this),
      schema: [],
      resultVisible: false,
      submitResult: '',
      resultType: 'success'
    }
  },
  computed: {
    actionName () {
      return this.$route.params.name
    },
    name () {
      return this.$store.state.actionDefinition.name || '加载中...'
    },
    description () {
      return this.$store.state.actionDefinition.desc || '加载中...'
    }
  },
  methods: {
    loadFormDefinition () {
      this.formData = {}
      HRequest.get('/api/action/' + this.actionName).then(
        (response) => this.formDefinitionHandler(response)
      )
    },
    formDefinitionHandler (response) {
      console.log(response)
      this.formData = {}
      let actionDefinition = response.data.data
      this.$store.dispatch('updateActionDefinition', actionDefinition).then(this.reloadSchema())
    },
    handleSubmit (e) {
      e.preventDefault()
      this.form.validateFields((err, values) => {
        if (!err) {
          console.log('Received values of form: ', values)
          // validate success, let us proceed.
          let submitURL = '/api/action/' + this.actionName
          const qs = require('qs')
          const options = {
            method: 'POST',
            headers: { 'content-type': 'application/x-www-form-urlencoded' },
            data: qs.stringify(this.formData),
            url: submitURL}
          HRequest(options).then((response) => {
            this.handleSubmitResult(response)
          })
        }
      })
    },
    handleSubmitResult (response) {
      console.log(response)
      this.resultVisible = true
      this.submitResult = response.data.data.msg
      this.resultType = response.data.data.msg_level
    },
    reloadSchema () {
      let formSchema = []
      let aParams = this.$store.state.actionDefinition.params
      for (let [name, value] of Object.entries(aParams)) {
        if (value.immutable) {
          continue
        }
        let fieldDefinition = {}
        // shared property of all types
        fieldDefinition.name = name
        fieldDefinition.required = value.required || false
        fieldDefinition.extra = value.description
        fieldDefinition.default = value.default
        // 判断类型
        if (value.type === 'boolean') {
          console.log('something')
          fieldDefinition.fieldType = 'CheckBoxInput'
        } else {
          if (value.enum) {
            // 下拉选择框
            fieldDefinition.fieldType = 'SelectInput'
            fieldDefinition.options = value.enum
          } else {
            // 普通输入框
            fieldDefinition.fieldType = 'TextInput'
          }
        }
        formSchema.push(fieldDefinition)
      }
      this.schema = formSchema
    },
    clearSubmitResult () {
      this.resultVisible = false
      this.submitResult = ''
      this.resultType = 'success'
    }
  },

  mounted () {
    this.loadFormDefinition()
  },
  watch: {
    '$route' (to, from) {
      // 对路由变化作出响应...
      this.loadFormDefinition()
      this.clearSubmitResult()
    }
  }

}
</script>

<style scoped>

</style>
