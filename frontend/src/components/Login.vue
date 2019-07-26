<template>
  <a-layout :style="{ minHeight: '100vh' }">
    <a-layout-content>
      <a-row type="flex" justify="center" align="middle" :style="{ minHeight: '80vh' }">
        <a-col :span="6">
          <p> Login </p>
          <a-form
            :form="form"
            class="login-form"
            @submit="handleSubmit"
          >
            <a-form-item>
              <a-input
                v-decorator="[
                  'username',
                  { rules: [{ required: true, message: 'Please input your username!' }] }
                ]"
                placeholder="Username"
              >
                <a-icon
                  slot="prefix"
                  type="user"
                  style="color: rgba(0,0,0,.25)"
                />
              </a-input>
            </a-form-item>
            <a-form-item>
              <a-input
                v-decorator="[
                  'password',
                  { rules: [{ required: true, message: 'Please input your Password!' }] }
                ]"
                type="password"
                placeholder="Password"
              >
                <a-icon
                  slot="prefix"
                  type="lock"
                  style="color: rgba(0,0,0,.25)"
                />
              </a-input>
            </a-form-item>
            <a-form-item>
              <a-button
                type="primary"
                html-type="submit"
                class="login-form-button"
              >
                Log in
              </a-button>
            </a-form-item>
          </a-form>
        </a-col>
      </a-row>
    </a-layout-content>
    <h-footer></h-footer>
  </a-layout>
</template>

<script>
import HFooter from './HFooter'
import {HRequest} from '../utils/HRequests'
export default {
  name: 'Login',
  components: {HFooter},
  beforeCreate () {
    this.form = this.$form.createForm(this)
  },
  methods: {
    handleSubmit (e) {
      e.preventDefault()
      this.form.validateFields((err, values) => {
        // ``values`` stands for the form data
        if (!err) {
          const qs = require('qs')
          let message = this.$message
          const options = {
            method: 'POST',
            headers: { 'content-type': 'application/x-www-form-urlencoded' },
            data: qs.stringify({
              user: values.username,
              password: values.password
            }),
            url: '/api/auth/login'}
          HRequest(options).then(
            (response) => {
              // the initial ``data`` is data in response object
              // second ``data`` is the data in message object
              if (response.data.data.success) {
                this.onSuccess()
              } else {
                message.warning(response.data.data.msg)
              }
            }
          )
        }
      })
    },
    onSuccess () {
      let next = this.$route.query.next
      if (next) {
        this.$router.push(next)
      } else {
        this.$router.push({name: 'Home'})
      }
    },
    purgeUserProfile () {
      this.$store.dispatch('deleteUserProfile')
    }
  }
}
</script>

<style scoped>

</style>
