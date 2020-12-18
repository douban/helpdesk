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
            :value="formData"
            @input="handleInput">
          </dynamic-form>
          <a-form-item
            :wrapper-col="{ span: 12, offset: 5 }"
          >
            <a-button type="primary" @click="handleSubmit" :disabled="!canSubmit">Submit</a-button>
            <a-modal
              v-model="showSubmitOK"
              title="Submit success!"
              ok-text="Go detail"
              cancel-text="Submit another"
              @ok="gotoTicketDetail"
              @cancel="showSubmitOK = false"
            >
              <p>Ticket: {{this.submitResponse.ticket.title}}, id: {{this.submitResponse.ticket.id}}</p>
              <p>You can stay here to submit another one</p>
              <p>Or check the ticket result now.</p>
            </a-modal>
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
import Ajv from 'ajv'
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
      submitResponse: {
        'ticket': 'dummy ticket',
        'id': 0
      },
      submitResult: '',
      resultType: 'success',
      actionDefinition: '',
      spinning: false,
      delayTime: 500,
      showSubmitOK: false,
      formAjv: new Ajv()
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
      HRequest.get('/api/action/' + this.actionName).then((response) => {
          this.formDefinitionHandler(response)
          this.handelBackfill(this.$route.query.backfill)
        }
      )
    },
    handelBackfill (backfillNum) {
      if (backfillNum && Number(backfillNum) > 0) {
        const notificationTitle = "Rerun ticket " + backfillNum + " error"
        HRequest.get('/api/ticket/' + backfillNum).then(
          (response) => {
            const ticketsLen = response.data.data.tickets.length
            if (ticketsLen == 1) {
              const isTheSameAction = this.$route.path.endsWith(response.data.data.tickets[0].provider_object)
              const ticket = response.data.data.tickets[0]
              if (isTheSameAction) {
                this.handleInput(ticket.params)
              } else {
                this.errorAsNotification(
                  notificationTitle,
                  "The backfill ticket should be the same action ticket, but ticket " + backfillNum + "'s action was: " + ticket.provider_object
                )
              }
            } else {
              this.errorAsNotification(
                "Rerun ticket " + backfillNum + " error",
                "Expect exactly 1 ticket info but got " + ticketsLen + "item(s)"
              )
            }
          }
        ).catch((error) => {
          this.errorAsNotification(
            notificationTitle,
            error.response.data.data.description
          )
        })
      }
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
          
          // airflow json schema verify
          if (this.actionDefinition.provider_type==='airflow' && this.actionDefinition.params_json_schema) {
            let validate = this.formAjv.compile(this.actionDefinition.params_json_schema)
            let jsonFormData = {}
            for (let [name, data] of Object.entries(this.formData)) {
              if (!data) {
                continue
              }
              
              // prevent json schema not covered this field
              var fieldType
              if (this.actionDefinition.params_json_schema.properties[name]) {
                fieldType = this.actionDefinition.params_json_schema.properties[name].type
              } else {
                fieldType = null
              }
              
              // trans hacked form data to json schema data and validate them
              if (fieldType === 'array') {
                jsonFormData[name] = data.split(',')
              } else if (fieldType === "integer") {
                jsonFormData[name] = parseInt(data)
              } else if (fieldType === "number") {
                jsonFormData[name] = Number(data)
              } else {
                jsonFormData[name] = data
              }
            }
            let isvalidate = validate(jsonFormData)
           
            if (!isvalidate) {
              this.submitResult = this.formAjv.errorsText(validate.errors)
              this.resultType = 'error'
              this.resultVisible = true
              this.canSubmit = true
              return
            }
          }

          const options = {
            method: 'POST',
            headers: { 'content-type': 'application/x-www-form-urlencoded' },
            data: qs.stringify(this.formData),
            url: submitURL}
          HRequest(options).then((response) => {
            this.handleSubmitResult(response)
            this.showSubmitOK = true
          }).finally(() => {
            this.canSubmit = true
          })
        } else {
          // validate failed, make the form submittable again
          this.canSubmit = true
        }
      })
    },
    handleSubmitResult (response) {
      this.resultVisible = true
      this.submitResponse = response.data.data
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
    },
    gotoTicketDetail () {
      this.$router.push({ name: 'HTicketDetail', params: { id: this.submitResponse.ticket.id }})
    },
    errorAsNotification (title, rawMsg) {
      const msg = rawMsg.length > 300 ? rawMsg.slice(0, 300) + '... ' : rawMsg
      this.$notification.title = rawMsg
      this.$notification.open({
        message: title,
        description: msg,
        duration: 0
      })
    },
  },

  mounted () {
    this.loadFormDefinition()
  },
  watch: {
    '$route' () {
      // reload form when route changes
      this.loadFormDefinition()
      this.clearSubmitResult()
    }
  }

}
</script>

<style scoped>

</style>
