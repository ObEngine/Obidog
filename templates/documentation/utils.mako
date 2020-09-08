<%def name="link_with_icon(text, url, icon)">
<div class="column is-1">
    <span>
        <i class="${icon}" aria-hidden="true"></i>
        <span class="has-text-info is-size-6"><a href="${url}">${text}</a></span>
    </span>
</div>
</%def>