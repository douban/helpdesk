<template>
  <a-layout :style="{ background: '#fff', padding: '24px', margin: '0 0 0 24px', minHeight: '280px' }">
    <a-divider orientation="left"><h3>{{name}}</h3></a-divider>

    <a-alert
      :message="description"
      type="info"
      :style="{ margin: '16px' }"
    >
    </a-alert>
    <a-col :span="12" :offset="3">
      <a-form
      :form="form"
      @submit="handleSubmit">
        <dynamic-form
          :schema="schema"
          v-model="formData">
        </dynamic-form>
        <a-button @click="handleSubmit">Submit</a-button>
      </a-form>
    </a-col>
  </a-layout>

</template>

<script>
import DynamicForm from './DynamicForm'
import {HRequest} from '../utils/HRequests'
export default {
  name: 'HForm',
  components: {
    DynamicForm
  },
  data () {
    return {
      formData: {
        firstName: 'Evan'
      },
      form: this.$form.createForm(this),
      schema: []
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
        }
      })
    },
    reloadSchema () {
      let formSchema = []
      let aParams = this.$store.state.actionDefinition.params
      for (let [name, value] of Object.entries(aParams)) {
        if (value.immutable) {
          continue
        }
        let fieldDefinition = {}

        fieldDefinition.name = name
        fieldDefinition.required = value.required || false
        fieldDefinition.extra = value.description
        fieldDefinition.default = value.default
        // 判断类型
        if (value.type === 'boolean') {
          console.log('something')
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
    }
  },
  mounted () {
    this.loadFormDefinition()
  },
  watch: {
    '$route' (to, from) {
      // 对路由变化作出响应...
      this.loadFormDefinition()
    }
  }

}
</script>

<style scoped>

</style>
