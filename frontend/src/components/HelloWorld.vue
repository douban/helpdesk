<template>
  <h-base>
    <a-layout class="padding24px">
      <a-row>
        <a-col :span="6">
          <a-layout class="whiteBackground" width="300">
            <h-sider></h-sider>
          </a-layout>
        </a-col>
        <a-col :span="18" >
          <a-layout :style="{ background: '#fff', padding: '24px', margin: '0 0 0 24px', minHeight: '280px' }">
            <a-divider orientation="left"><h3>申请服务器账号/重置密码</h3></a-divider>

            <a-alert
              message="申请 ssh 登录服务器的账号，或者重置密码"
              type="info"
              :style="{ margin: '16px' }"
            >
            </a-alert>
            <a-col :span="12" :offset="3">
              <h-form
              :schema="schema"
              v-model="formData">
              </h-form>
            </a-col>
          </a-layout>
        </a-col>
      </a-row>
      <h-drawer v-if="this.$store.isAdmin"></h-drawer>
    </a-layout>
  </h-base>
</template>

<script>
import HSider from './HSider'
import HForm from './HForm'
import HDrawer from './HDrawer'
import HBase from './HBase'
export default {
  name: 'HelloWorld',
  components: {
    HDrawer,
    'h-sider': HSider,
    'h-form': HForm,
    'h-base': HBase
  },
  data () {
    return {
      msg: 'Welcome to Your Vue.js App',
      schema: [
        {
          fieldType: 'TextInput',
          placeholder: 'First Name',
          label: 'First Name',
          name: 'firstName'
        },
        {
          fieldType: 'TextInput',
          placeholder: 'Last Name',
          label: 'Last Name',
          name: 'lastName'
        },
        {
          fieldType: 'NumberInput',
          placeholder: 'Age',
          name: 'age',
          label: 'Age',
          minValue: 0
        }
      ],
      formData: {
        firstName: 'Evan'
      }
    }
  }
}
</script>

<!-- Add "scoped" attribute to limit CSS to this component only -->
<style scoped>
  .padding24px {
    padding: 0px 24px 24px;
  }
  .whiteBackground {
    background: #fff
  }
</style>
