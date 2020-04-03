<template>
  <a-spin tip="Loading ..." :spinning="spinning" :delay="delayTime">
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
            @input="handleInput">
          </dynamic-form>
          <a-form-item
            :wrapper-col="{ span: 12, offset: 5 }"
          >
            <a-button type="primary" @click="handleSubmit" :disabled="!canSubmit">Submit</a-button>
          </a-form-item>
        </a-form>
      </a-col>
      <h-drawer v-if="this.$store.getters.isAdmin" :actionDefinition="this.actionDefinition"></h-drawer>
    </a-layout>
  </a-spin>

</template>

<script>
import DynamicForm from './DynamicForm'
import {HRequest} from '../utils/HRequests'
import AFormItem from 'ant-design-vue/es/form/FormItem'
import HDrawer from '@/components/HDrawer'
export default {
  name: 'HForm',
  components: {
    AFormItem,
    DynamicForm,
    HDrawer
  },
  data () {
    return {
      formData: {},
      form: this.$form.createForm(this),
      resultVisible: false,
      canSubmit: true,
      submitResult: '',
      resultType: 'success',
      actionDefinition: '',
      spinning: false,
      delayTime: 500
    }
  },
  computed: {
    actionName () {
      return this.$route.params.name
    },
    name () {
      return this.actionDefinition.name || 'Loading...'
    },
    description () {
      return this.actionDefinition.desc || 'Loading...'
    },
    schema () {
      let formSchema = []
      let aParams = this.actionDefinition.params
      if (aParams === undefined) {
        // in case actionDefinition is not loaded yet
        return formSchema
      }
      for (let [name, param] of Object.entries(aParams)) {
        if (param.immutable) {
          continue
        }
        let fieldDefinition = {}
        // shared property of all types
        fieldDefinition.name = name
        fieldDefinition.required = param.required || false
        fieldDefinition.extra = param.description
        fieldDefinition.default = param.default
        // param.type indicate which widget to use
        if (param.type === 'boolean') {
          fieldDefinition.fieldType = 'CheckBoxInput'
        } else {
          if (param.enum) {
            // SelectInput
            fieldDefinition.fieldType = 'SelectInput'
            fieldDefinition.options = param.enum
          } else {
            // Normal TextInput
            fieldDefinition.fieldType = 'TextInput'
          }
        }
        formSchema.push(fieldDefinition)
      }
      return formSchema
    }
  },
  methods: {
    loadFormDefinition () {
      this.spinning = true
      this.resetForm()
      HRequest.get('/api/action/' + this.actionName).then(
        (response) => this.formDefinitionHandler(response)
      )
    },
    resetForm () {
      this.form.resetFields()
      this.formData = {}
    },
    formDefinitionHandler (response) {
      this.resetForm()
      this.actionDefinition = response.data.data
      this.spinning = false
    },
    handleSubmit (e) {
      e.preventDefault()
      this.canSubmit = false
      this.form.validateFields((err, values) => {
        if (!err && values) {
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
          }).finally(() => {
            this.canSubmit = true
          })
        }
      })
    },
    handleSubmitResult (response) {
      this.resultVisible = true
      this.submitResult = response.data.data.msg
      this.resultType = response.data.data.msg_level
    },
    clearSubmitResult () {
      this.resultVisible = false
      this.submitResult = ''
      this.resultType = 'success'
    },
    handleInput (data) {
      this.form.setFieldsValue(data)
      this.formData = data
    }
  },

  mounted () {
    this.loadFormDefinition()
  },
  watch: {
    '$route' (to, from) {
      // reload form when route changes
      this.loadFormDefinition()
      this.clearSubmitResult()
    }
  }

}
</script>

<style scoped>

</style>
