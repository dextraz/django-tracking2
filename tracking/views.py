import logging

from datetime import timedelta, datetime
from functools import reduce
from collections import defaultdict, OrderedDict

from django.shortcuts import (
    render,
    get_object_or_404,
)
from django.http import HttpResponseNotFound
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import permission_required
from django.db.models import Count, Avg, Sum
from django.core.paginator import Paginator

from chartjs.views.lines import BaseLineChartView

from tracking.models import Visitor, Pageview
from tracking.settings import (
    TRACK_PAGEVIEWS,
    TRACK_PAGING_SIZE,
    TRACK_USING_GEOIP,
)
from tracking.utils import processTimeRangeForm

log = logging.getLogger(__file__)

@permission_required('tracking.visitor_log')
def dashboard(request):
    (start_time, end_time, track_start_time, warn_incomplete, form) = processTimeRangeForm(request)

    # queries take `date` objects (for now)
    user_stats = Visitor.objects.user_stats(start_time, end_time)
    visitor_stats = Visitor.objects.stats(start_time, end_time)
    for us in user_stats:
        us.time_on_site = timedelta(seconds=us.time_on_site)
    if TRACK_PAGEVIEWS:
        pageview_stats = Pageview.objects.stats(start_time, end_time)
    else:
        pageview_stats = None

    context = {
        'form': form,
        'track_start_time': track_start_time,
        'warn_incomplete': warn_incomplete,
        'user_stats': user_stats,
        'visitor_stats': visitor_stats,
        'pageview_stats': pageview_stats,
        'start_time': start_time,
        'end_time': end_time,
        'has_pageviews': TRACK_PAGEVIEWS,
    }
    return render(request, 'tracking/dashboard.html', context)

@permission_required('tracking.visitor_log')
def visitor_overview(request, user_id):
    (start_time, end_time, track_start_time, warn_incomplete, form) = processTimeRangeForm(request)

    page = request.GET.get('page', 1)
    # queries take `date` objects (for now)
    user = Visitor.objects.user_stats(start_time, end_time).filter(pk=user_id).first()
    if user:
        user.time_on_site = timedelta(seconds=user.time_on_site)
    else:
        # User did not visit at all during this period. Need name but not stats
        user = get_object_or_404(get_user_model(), pk=user_id)
    visits = Visitor.objects.filter(user=user, start_time__range=(start_time, end_time))
    paginator = Paginator(visits, TRACK_PAGING_SIZE)
    log.critical(visits)

    context = {
        'form': form,
        'track_start_time': track_start_time,
        'warn_incomplete': warn_incomplete,
        'visits': paginator.page(page),
        'user': user,
        'start_time': start_time,
        'end_time': end_time,
        'has_geoip': TRACK_USING_GEOIP,
    }
    return render(request, 'tracking/visitor_overview.html', context)

@permission_required('tracking.visitor_log')
def visitor_detail(request, visit_id):
    pvpage = request.GET.get('pvpage', 1)
    pvspage = request.GET.get('pvspage', 1)
    visit = get_object_or_404(Visitor, pk=visit_id)
    visit.time_on_site = timedelta(seconds=visit.time_on_site)
    pvcount = visit.pageviews.count()
    pageviews = visit.pageviews.order_by('-view_time')
    pageview_stats = visit.pageviews.values('method', 'url').annotate(views=Count('url')).order_by('-views')
    pvspaginator = Paginator(pageview_stats, TRACK_PAGING_SIZE)
    pvpaginator = Paginator(pageviews, TRACK_PAGING_SIZE)

    context = {
        'visit': visit,
        'pageviews': pvpaginator.page(pvpage),
        'pageview_stats': pvspaginator.page(pvspage),
        'pvcount': pvcount,
        'avg_time_per_page': visit.time_on_site/pvcount if pvcount else None
    }
    return render(request, 'tracking/visitor_detail.html', context)

@permission_required('tracking.visitor_log')
def visitor_page_detail(request, user_id):
    try:
        page_url = request.GET['page_url']
    except:
        return HttpResponseNotFound()   

    (start_time, end_time, track_start_time, warn_incomplete, form) = processTimeRangeForm(request)

    page = request.GET.get('page', 1)
    user = get_object_or_404(get_user_model(), pk=user_id)
    relevant_visits = Visitor.objects.filter(
        pageviews__url=page_url,
        user__pk=user_id,
        start_time__lt=end_time,
    )
    if start_time:
        relevant_visits = relevant_visits.filter(start_time__gte=start_time)
    else:
        relevant_visits = relevant_visits.filter(start_time__isnull=False)
    
    aggs = relevant_visits.values('pk').annotate(views=Count('pageviews')).aggregate(
        Avg('views'),
        Sum('views')
    )
    visits = relevant_visits.distinct().order_by(
        'end_time',
        'start_time'
    )
    paginator = Paginator(visits, TRACK_PAGING_SIZE)

    context = {
        'total_views': aggs['views__sum'] if aggs['views__sum'] else 0,
        'avg_views_per_visit': aggs['views__avg'] if aggs['views__avg'] else 0,
        'visits': paginator.page(page),
        'user': user,
        'page_url': page_url,
        'form': form,
        'track_start_time': track_start_time,
        'warn_incomplete': warn_incomplete,
        'start_time': start_time,
        'end_time': end_time,
        'has_geoip': TRACK_USING_GEOIP,
    }
    return render(request, 'tracking/visitor_page_detail.html', context)

@permission_required('tracking.visitor_log')
def visitor_pageview_detail(request, user_id, pageview_id):
    pageview = get_object_or_404(Pageview, pk=pageview_id, visitor__user_id=user_id)
    next_pv = Pageview.objects.filter(
        visitor__user_id=user_id,
        view_time__gt=pageview.view_time,
    ).order_by('view_time').first()
    if next_pv:
        duration = next_pv.view_time - pageview.view_time
    else:
        duration = None

    context = {
        'pageview': pageview,
        'duration': duration,
    }
    return render(request, 'tracking/visitor_pageview_detail.html', context)

@permission_required('tracking.visitor_log')
def page_overview(request):
    (start_time, end_time, track_start_time, warn_incomplete, form) = processTimeRangeForm(request)

    page = request.GET.get('page', 1)
    relevant_pvs = Pageview.objects.filter(view_time__lt=end_time)
    if start_time:
        relevant_pvs = relevant_pvs.filter(view_time__gte=start_time)
    pageview_counts = relevant_pvs.values('url').annotate(views=Count('url')).order_by('-views')
    paginator = Paginator(pageview_counts, TRACK_PAGING_SIZE)

    context = {
        'pageview_counts': paginator.page(page),
        'total_page_views': reduce(lambda acc, c: acc + c['views'], pageview_counts, 0),
        'total_pages': len(pageview_counts),
        'form': form,
        'track_start_time': track_start_time,
        'warn_incomplete': warn_incomplete,
        'start_time': start_time,
        'end_time': end_time,
    }
    return render(request, 'tracking/page_overview.html', context)

@permission_required('tracking.visitor_log')
def page_detail(request):
    try:
        page_url = request.GET['page_url']
    except:
        return HttpResponseNotFound()   

    (start_time, end_time, track_start_time, warn_incomplete, form) = processTimeRangeForm(request)

    page = request.GET.get('page', 1)
    relevant_pvs = Pageview.objects.filter(view_time__lt=end_time)
    if start_time:
        relevant_pvs = relevant_pvs.filter(view_time__gte=start_time)
    pageviews = relevant_pvs.filter(url=page_url).order_by('-view_time')
    pv_count = pageviews.count()
    uniqueVisitors = relevant_pvs.values('visitor_id').distinct().count()
    paginator = Paginator(pageviews, TRACK_PAGING_SIZE)

    context = {
        'total_views': pv_count,
        'visitors': uniqueVisitors,
        'pageviews': paginator.page(page),
        'page_url': page_url,
        'form': form,
        'track_start_time': track_start_time,
        'warn_incomplete': warn_incomplete,
        'start_time': start_time,
        'end_time': end_time,
    }
    return render(request, 'tracking/page_detail.html', context)

class UserBasedPageChartJson(BaseLineChartView):

    def get_labels(self):
        return [d.isoformat() for d in self._get_time_list()]

    def get_providers(self):
        """Return names of datasets."""
        return list(self._get_user_dates_dict().keys())

    def get_options(self):
        pass

    def get_data(self):
        retList = []
        dates = self._get_time_list()
        for dDict in self._get_user_dates_dict().values():
            userViewCounts = [dDict.get(d, 0) for d in dates]
            retList.append(userViewCounts)
        return retList

    def _get_user_dates_dict(self):
        # memoized method
        if not hasattr(self, 'userDatesDict'):
            # build userDatesDict
            page_url = self.request.GET.get('page_url')
            (start_time, end_time, _, _, _) = processTimeRangeForm(self.request)
            pvs = Pageview.objects.filter(
                url=page_url,
                view_time__range=(start_time, end_time),
            ).order_by(
                'view_time',
            ).values(
                'view_time',
                'visitor__user__username',
            )
            # Bin pageview counts by username and date
            self.userDatesDict = OrderedDict()
            for pv in pvs:
                u = pv['visitor__user__username']
                d = pv['view_time'].date()
                if u not in self.userDatesDict:
                    self.userDatesDict[u] = OrderedDict()
                if d not in self.userDatesDict[u]:
                    self.userDatesDict[u][d] = 0
                self.userDatesDict[u][d] += 1
        return self.userDatesDict

    def _get_time_list(self):
        # memoized method
        if not hasattr(self, 'timeList'):
            # find min and max dates in data
            dDicts = self._get_user_dates_dict().values()
            minDate = datetime.fromtimestamp(2**32).date()
            maxDate = datetime.fromtimestamp(0).date()
            for dDict in dDicts:
                dates = list(dDict.keys())
                minDate = min(minDate, dates[0])
                maxDate = max(maxDate, dates[-1])
            # create labels of every date between min and max
            numDays = (maxDate - minDate).days
            self.timeList = [minDate + timedelta(days=n) for n in range(0, numDays)]
        return self.timeList
