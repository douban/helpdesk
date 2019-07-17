<template functional>
  <a-sub-menu
    :key="props.menuInfo.key"
  >
    <span slot="title">
      <span>{{ props.menuInfo.title }}</span>
    </span>
    <template v-for="item in props.menuInfo.children">
      <a-menu-item
        v-if="!item.children"
        :key="item.key"
      >
        <a v-if="item.url" :href="'/#/forms/' + item.name" >{{item.title}}</a>
        <span v-else>{{item.title}}</span>
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
