<template>
  <a-layout :style="{ minHeight: '100vh' }">
    <a-layout-content>
      <a-row type="flex" justify="center" align="middle">
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
const axios = require('axios')
export default {
  name: 'Login',
  components: {HFooter},
  beforeCreate () {
    this.form = this.$form.createForm(this)
  },
  mounted () {
    this.checkUserLoginStatus()
  },
  methods: {
    handleSubmit (e) {
      e.preventDefault()
      this.form.validateFields((err, values) => {
        // values 是表单对象
        if (!err) {
          const qs = require('qs')
          let message = this.$message
          console.log('Received values of form: ', values)
          const options = {
            method: 'POST',
            headers: { 'content-type': 'application/x-www-form-urlencoded' },
            data: qs.stringify({
              user: values.username,
              password: values.password
            }),
            url: '/api/auth/challenge'}
          HRequest(options).then(
            (response) => {
              // 第一个data 是response 里的data , 第二个data 是消息体内的data
              if (response.data.data.success) {
                console.log('验证成功')
                console.log(response.data)
                this.onSuccess()
              } else {
                console.log('验证失败')
                console.log(response)
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
        this.$router.push('/')
      }
    },
    purgeUserProfile () {
      this.$store.dispatch('deleteUserProfile')
      // TODO 在localstorage 删除
    },
    checkUserLoginStatus () {
      axios.get('/api/auth/heartbeat').then(
        (response) => {
          if (response.data.data.status_code === 200) {
            this.onSuccess()
          }
        })
    }
  }
}
</script>

<style scoped>

</style>
