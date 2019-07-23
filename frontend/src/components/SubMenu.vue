<template functional>
  <a-sub-menu
    :key="props.menuInfo.name"
  >
    <span slot="title">
      <a-icon type="folder" />
      <span>{{ props.menuInfo.name }}</span>
    </span>
    <template v-for="item in props.menuInfo.children">
      <a-menu-item
        v-if="!item.children"
        :key="item.name"
      >
        <a v-if="item.target_object" :href="'/#/forms/' + item.target_object" >{{item.name}}</a>
        <span v-else>{{item.name}}</span>
      </a-menu-item>
      <sub-menu
        v-else
        :key="item.name"
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
