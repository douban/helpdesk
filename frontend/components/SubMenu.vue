<template functional>
  <a-sub-menu
    :key="props.menuInfo.key"
  >
    <span slot="title">
      <a-icon type="folder" />
      <span>{{ props.menuInfo.name }}</span>
    </span>
    <template v-for="item in props.menuInfo.children">
      <a-menu-item
        v-if="!item.children"
        :key="item.key"
      >
        <router-link v-if="item.target_object"
                     :to="{ name: 'action', params: { action: item.target_object }}"
                     :title="item.desc"
        >
          {{item.name}}
        </router-link>
        <span v-else>{{item.name}}</span>
      </a-menu-item>
      <sub-menu
        v-else
        :key="item.key"
        :menu-info="item"
      />
    </template>
  </a-sub-menu>
</template>
<script>
export default {
  props: ['menuInfo']
}
</script>
