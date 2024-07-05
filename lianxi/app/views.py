from django.forms import BaseModelForm
from django.shortcuts import render,get_object_or_404,redirect
from .models import Border,Topic, Post
from django.http import HttpResponse
from django.http import Http404
from django.contrib.auth.models import User
from django.db.models import Count
from .forms import NewTopicForm
from django.contrib.auth.decorators import login_required
from .forms import PostForm
from .models import Topic
from django.views.generic import View
from django.views.generic import CreateView
from django.urls import reverse_lazy
from django.views.generic import UpdateView
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views.generic import ListView
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.utils.decorators import	method_decorator
from django.views.generic	import	UpdateView
from django.urls import reverse

# ... 其他代码 ...



# Create your views here.



@login_required
def reply_topic(request,pk,topic_pk):
    topic = get_object_or_404(Topic, border__pk=pk, pk=topic_pk)
    if request.method == 'POST':
        form = PostForm(request.POST)
        if form.is_valid():
                post = form.save(commit=False)
                post.topic = topic
                post.created_by = request.user
                post.save()
                topic.last_update	=	timezone.now()
                topic.save()
                topic_url = reverse('topic_posts',	kwargs={'pk':pk,'topic_pk':	topic_pk})
                topic_post_url ='{url}?page={page}#{id}'.format(
                     url=topic_url,
                      id=post.pk,
                      page=topic.get_page_count()
                       )
                return redirect(topic_post_url)
    else:
        form = PostForm()
    return render(request,'reply_topic.html',{'topic':topic,'form':form})

def new_topic(request,pk):
    board = get_object_or_404(Border,pk=pk)
    if request.method == 'POST':
        form = NewTopicForm(request.POST)
        if form.is_valid():
            topic = form.save(commit=False)
            topic.border = board
            topic.starter = request.user
            topic.save()
            Post.objects.create(message=form.cleaned_data.get('message'),topic=topic,created_by=request.user)
            return redirect('topic_posts', pk=pk, topic_pk=topic.pk)
    else:
        form = NewTopicForm()
    return render(request,'new_topic.html',{'board':board,'form':form})




def topic_posts(request, pk, topic_pk):
    topic = get_object_or_404(Topic, border__pk=pk, pk=topic_pk)
    topic.views += 1
    topic.save()
    return render(request, 'topic_posts.html', {'topic': topic})
def board_topics(request,pk):
    board = get_object_or_404(Border,pk=pk)
    queryset = board.topics.order_by('-last_update').annotate(replies=Count('posts')-1)
    page = request.GET.get('page', 1)
    paginator = Paginator(queryset, 20)
    try:
        topics = paginator.page(page)
    except PageNotAnInteger:
        topics = paginator.page(1)
    except EmptyPage:
        topics = paginator.page(paginator.num_pages)
    return render(request,'topics.html',{'board':board,'topics': topics})


def new_post(request):
    if request.method == 'POST':
        form = PostForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('post_list')
    else:
        form = PostForm()
    return render(request,'new_post.html',{'form':form})


class NewPostView(CreateView):
    model = Post
    form_class = PostForm
    success_url = reverse_lazy('post_list')
    template_name = 'new_post.html'
    def render_form(self,request):
        return render(request,'new_post.html',{'form':self.form})
    def post(self,request):
        self.form = PostForm(request.POST)
        if self.form.is_valid():
            self.form.save()
            return redirect('post_list')
    def get(self,request):
        self.form = PostForm()
        return self.render(request)

@method_decorator(login_required, name='dispatch')
class PostUpdateView(UpdateView):
    model = Post
    fields = ('message',)
    template_name = 'edit_post.html'
    pk_url_kwarg = 'post_pk'
    context_object_name = 'post'

    def get_queryset(self):
        queryset = super().get_queryset()
        return queryset.filter(created_by=self.request.user)

    def form_valid(self, form):
        post = form.save(commit=False)
        post.updated_by = self.request.user
        post.updated_at = timezone.now()
        post.save()
        return redirect('topic_posts', pk=post.topic.border.pk, topic_pk=post.topic.pk)
    
class BoardListView(ListView):
    model = Border
    context_object_name = 'boards'
    template_name = 'index.html'

class TopicListView(ListView):
    model = Topic
    context_object_name = 'topics'
    template_name = 'topics.html'
    paginate_by = 10

    def get_context_data(self, **kwargs):
        kwargs['border'] = self.border
        return super().get_context_data(**kwargs)
    def get_queryset(self):
        self.border = get_object_or_404(Border, pk=self.kwargs.get('pk'))
        queryset = self.border.topics.order_by('-last_update').annotate(replies=Count('posts')-1)
        return queryset
   
class PostListView(ListView):
    model = Post
    context_object_name = 'posts'
    template_name = 'topic_posts.html'
    paginate_by = 2

    def get_context_data(self, **kwargs):
        session_key	='viewed_topic_{}'.format(self.topic.pk)
        self.topic.views += 1
        self.topic.save()
        self.request.session[session_key] =True
        kwargs['topic'] = self.topic
        return super().get_context_data(**kwargs)
       
    def get_queryset(self):
        self.topic = get_object_or_404(Topic, border__pk=self.kwargs.get('pk'), pk=self.kwargs.get('topic_pk'))
        queryset = self.topic.posts.order_by('created_at')
        return queryset
    